"""
Simple script to refresh references.
"""
import pymysql
import datetime as dt
import sys
from collections import namedtuple
def __help__():
    print('Helper to update reference values to the snap-reports mysql database with specific ref branch.')
    print('update_ref.py DB_USER:DB_PASSWORD@DB_HOST:DB_PORT/DB_NAME ref_tag')

def __args__():
    args = sys.argv[1:]
    if '-h' in args:
        __help__()
        sys.exit(0)

    if len(args) != 2:
        print('Error: wrong number of arguments')
        __help__()
        sys.exit(2)
    db_info = __parse_db_arg__(args[0])
    graph_path = args[1]

    return db_info, graph_path


def __parse_db_arg__(arg):
    if '@' not in arg or ':' not in arg:
        print('Error: malformed DB connection informations')
        __help__()
        sys.exit(2)

    userinfo, conninfo = arg.split('@')
    user, pwd = userinfo.split(':')
    conninfo, db_name = conninfo.split('/')
    host, port = conninfo.split(':')
    Info = namedtuple('Info', 'user password, host port db_name')
    return Info(user=user, password= pwd, host= host,
                port= port, db_name= db_name)

def __sum_tests__(a, b):
    c = {
        'test': a['test'],
    }
    for key in KEYS:
        c[key] = a[key] + b[key]
    return c

def selectQuery(ref_tag):
    query = """
    SELECT
        test, duration, cpu_time, cpu_usage_avg, cpu_usage_max,
        memory_avg, memory_max, io_write, io_read, threads_avg, threads_max
    FROM results
    WHERE
        job IN
            (SELECT MAX(id) FROM jobs WHERE dockerTag =
                (SELECT ID FROM dockerTags WHERE name = "snap:"""+ref_tag+""""));
    """
    return query

CLEAR_REFRENCES = """
DELETE FROM reference_values;
"""

KEYS = ["duration", "cpu_time", "cpu_usage_avg", "cpu_usage_max", "memory_avg",
    "memory_max", "io_read", "io_write", "threads_avg", "threads_max"]

def updateRefQuery(ref_tag):
    query = """
    INSERT INTO reference_values
        (ID,test, referenceTag, updated, duration, cpu_time, cpu_usage_avg,
        cpu_usage_max, memory_avg, memory_max, io_write, io_read, threads_avg,
        threads_max, raw_data)
    VALUES
        (%s,%s, (SELECT ID FROM dockerTags WHERE name = "snap:"""+ref_tag+""""), %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, b'');
    """
    return query


def __update_reference__(db, tests, ref_tag):
    cursor = db.cursor()
    cursor.execute(CLEAR_REFRENCES)
    updated = str(dt.datetime.now())
    db.commit()
    #(test, (SELECT ID FROM dockerTags WHERE name = "snap:"""+ref_tag+""""), updated,
        # duration, cpu_time, cpu_usage_avg, cpu_usage_max, memory_avg,
        # memory_max, io_write, io_read, threads_avg, threads_max, "")
    cursor.execute("""SELECT * FROM referenceTags""")
    uid = cursor.fetchone()['ID']
    print('uid: ',uid)
    for i, test_id in enumerate(tests):
        print(f'\r{i+1:>3}/{len(tests)}', end='')
        test = tests[test_id]
        test['updated'] = updated
        print(test,";",updated)
        cursor.execute(updateRefQuery(ref_tag), (i,test['test'],test['updated'],test['duration'],test['cpu_time'],test['cpu_usage_avg'],test['cpu_usage_max'],
                        test['memory_avg'],test['memory_max'],test['io_write'],test['io_read'],test['threads_avg'],test['threads_max']))
        db.commit()
    cursor.close()
    print()


if __name__ == "__main__":
    DB_INFO, REF_TAG = __args__()
    print("Update with ref: "+REF_TAG)
    DB = pymysql.connect(
        host=DB_INFO.host,
        port=int(DB_INFO.port),
        user=DB_INFO.user,
        password=DB_INFO.password,
        db=DB_INFO.db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = DB.cursor()

    cursor.execute("""SELECT * FROM referenceTags;""")
    rows = cursor.fetchall()
    print(rows)
    cursor.execute("""SELECT * FROM dockerTags;""")
    rows2 = cursor.fetchall()
    print(rows2)
    ##remove the reference_values and update the referenceTag with a new ID ref
    # cursor.execute(CLEAR_REFRENCES)
    # DB.commit()
    # cursor.execute("""UPDATE referenceTags SET ID = '29';""")
    # DB.commit()
    nb_rows = cursor.execute(selectQuery(REF_TAG))
    rows = cursor.fetchall()
    tests = {}
    tests_counter = {}
    for row in rows:
        test_id = row['test']
        if test_id not in tests:
            tests[test_id] = dict(row)
            tests_counter[test_id] = 1
        else:
            tests[test_id] = __sum_tests__(tests[test_id], row)
            tests_counter[test_id] += 1
    for test_id in tests:
        for key in KEYS:
            tests[test_id][key] /= tests_counter[test_id]
    cursor.close()
    print(len(tests))
    __update_reference__(DB, tests, REF_TAG)