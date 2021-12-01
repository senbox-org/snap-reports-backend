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

    if len(args) != 1:
        print('Error: wrong number of arguments')
        __help__()
        sys.exit(2)
    db_info = __parse_db_arg__(args[0])

    return db_info


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


if __name__ == "__main__":
    DB_INFO = __args__()
    DB = pymysql.connect(
        host=DB_INFO.host,
        port=int(DB_INFO.port),
        user=DB_INFO.user,
        password=DB_INFO.password,
        db=DB_INFO.db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = DB.cursor()
    cursor.execute("""SELECT * FROM dockerTags;""")
    rows = cursor.fetchall()
    print("listing dockerTags (=branches) ",rows)
    dockerTag = 'snap:gp_revert'
    remove = False
    cursor.execute('SELECT ID FROM dockerTags WHERE name = "'+dockerTag+'";')
    rows = cursor.fetchall()
    print("\ndockerTag ID: ",rows, " according to :",dockerTag)
    cursor.execute("""SELECT ID FROM jobs WHERE dockerTag = " """+str(rows[0]['ID'])+""" ";""")
    rows3 = cursor.fetchall()
    print("jobs ID: ",rows3)
    for row3 in rows3:
        print(row3)
        cursor.execute("""SELECT ID FROM results WHERE job = " """+str(row3['ID'])+""" ";""")
        rows2 = cursor.fetchall()
        print("remove results: ",rows2)

        cursor.execute("""SELECT * FROM jobs WHERE dockerTag = " """+str(row3['ID'])+""" ";""")
        rows4 = cursor.fetchall()
        print("remove jobs: ",rows4)
        if(remove):
            cursor.execute("""DELETE FROM results WHERE job =" """+str(row3['ID'])+""" ";""")
            DB.commit()
            cursor.execute("""DELETE FROM jobs WHERE ID = " """+str(row3['ID'])+""" ";""")
            DB.commit()

    rows5=[rows[0]['ID']]
    for row5 in rows5:
        print(row5)
        cursor.execute("""SELECT name FROM dockerTags WHERE ID = " """+str(row5)+""" ";""")
        rows2 = cursor.fetchall()
        print("remove dockertags: ",rows2)
        if(remove):
            cursor.execute("""DELETE FROM dockerTags WHERE ID = " """+str(row5)+""" ";""")
            DB.commit()
    
    
    cursor.execute("""SELECT * FROM dockerTags;""")
    rows = cursor.fetchall()
    print("\nResult after process :\n listing dockerTags (=branches) ",rows)