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



def selectQuery(ref_tag):
    query = """
    SELECT
        ID, job, test, duration, cpu_time, cpu_usage_avg, cpu_usage_max,
        memory_avg, memory_max, io_write, io_read, threads_avg, threads_max
    FROM results
    WHERE
        test = 270 AND job IN
            (SELECT id FROM jobs WHERE dockerTag =
                (SELECT ID FROM dockerTags WHERE name = "snap:"""+ref_tag+""""));
    """
    return query

def selectJobsQuery(ref_tag):
    query = """
    SELECT
        *
    FROM jobs
    WHERE
        dockerTag =
                (SELECT ID FROM dockerTags WHERE name = "snap:"""+ref_tag+"""");
    """
    return query

def clearJobs(ref_tag):
    query = """
    DELETE FROM jobs 
    WHERE
        ID = 1078 AND dockerTag =
                    (SELECT ID FROM dockerTags WHERE name = "snap:"""+ref_tag+"""");;
    """
    return query

def clearResult(ref_tag):
    query = """
    DELETE FROM results
    WHERE
        job = 1078 AND test = 270 AND job IN
            (SELECT id FROM jobs WHERE dockerTag =
                (SELECT ID FROM dockerTags WHERE name = "snap:"""+ref_tag+""""));
    """
    return query

KEYS = ["duration", "cpu_time", "cpu_usage_avg", "cpu_usage_max", "memory_avg",
    "memory_max", "io_read", "io_write", "threads_avg", "threads_max"]



if __name__ == "__main__":
    DB_INFO, REF_TAG = __args__()
    # print("Update with ref: "+REF_TAG)
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
    # print(rows)
    cursor.execute("""SELECT * FROM dockerTags;""")
    rows2 = cursor.fetchall()


    # cursor.execute(clearResult(REF_TAG))
    # DB.commit()
    cursor.execute(clearJobs(REF_TAG))
    DB.commit()
    nb_rows = cursor.execute(selectJobsQuery(REF_TAG))
    rows = cursor.fetchall()

    tests = {}
    tests3 = {}
    tests2 = {}
    tests_counter = {}
    IDs=[]
            
    for row in rows:
        
        print(row,"\n")
        # test_id = row['test']
        # if test_id not in tests:
        #     tests[test_id] = dict(row)
        #     tests2[test_id] = [dict(row)]
        #     tests_counter[test_id] = 1
        #     IDs.append(test_id)
        # else:
        #     tests2[test_id].append(dict(row))
        #     tests_counter[test_id] += 1

    cursor.close()

