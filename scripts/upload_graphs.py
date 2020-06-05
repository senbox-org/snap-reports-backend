"""
Upload XML GPT Graph to the reports MySQL DB.

author: Martino Ferrari
email: martino.ferrari@c-s.fr
"""
import pymysql
import sys
import os
from collections import namedtuple


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


def __help__():
    print('Helper to upload XML GPT grpah to the snap-reports mysql database.')
    print('   upload_graphs.py DB_USER:DB_PASSWORD@DB_HOST:DB_PORT/DB_NAME XML_GRAPH_PATH')


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


def retrive_tests(db):
    """
    Retrive stored tests.

    Paramters:
    ----------
     - db: mysql db connection

    Returns:
    --------
    list of tests with ID and graph path
    """
    with db.cursor() as cursor:
        query = '''SELECT ID, graphPath FROM tests;'''
        res = cursor.execute(query)
        print(f'Retriving {res} tests...')
        return list(cursor.fetchall())


def upload_graphs(db, tests, graph_path):
    """
    Upload XML graph to mysql database.

    Parameters:
    -----------
     - db: mysql db connection
     - tests: list of tests
     - graph_path: base path containing xml path
    """
    with db.cursor() as cursor:
        total = len(tests)
        for i, test in enumerate(tests):
            print(f'\rUploading: {i+1:>4}/{total}', flush=True, end='')
            path = os.path.join(graph_path, test['graphPath'])
            test_id = int(test['ID'])
            with open(path, 'r') as xml_file:
                text = xml_file.read().encode('utf-8')
                query = f"INSERT INTO test_graph (test, graph) VALUES ('{test_id}', {str(text)[1:]});"
                cursor.execute(query)
        print()
    db.commit()

if __name__ == "__main__":
    DB_INFO, GPT_PATH = __args__()
    DB = pymysql.connect(
        host=DB_INFO.host,
        port=int(DB_INFO.port),
        user=DB_INFO.user,
        password=DB_INFO.password,
        db=DB_INFO.db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    print('MySQL DB connected')
    TESTS = retrive_tests(DB)
    upload_graphs(DB, TESTS, GPT_PATH)
    print('Done')