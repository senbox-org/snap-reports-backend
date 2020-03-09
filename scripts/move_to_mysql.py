"""
Move sqlite reports db to MySQL remote server.

author: Martino Ferrari (CS Group)
email: martino.ferrari@c-s.fr
"""
import argparse
import sqlite3
import pymysql


def __args__():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', help='Source SQLite DB file')
    parser.add_argument('target', help='Target MySQL DB user:password@host:port/db')
    return parser.parse_args()



def init_mysql_db(connection):
    """
    Initialize MySQL database.
    """
    with open('assets/schema.sql', 'r') as schema_f:
        schema = schema_f.read()
        with connection.cursor() as cursor:
            cursor.execute(schema)
        connection.commit()


def __main__():
    args = __args__()
    src_db = sqlite3.connect(args.source)
    dbusr, dbpwd = args.target.split('@')[0].split(':')
    db_name = args.target.split('@')[1].split('/')[1]
    host, port = args.target.split('@')[1].split('/')[0].split(':')
    trg_db = pymysql.connect(
        host=host,
        port=int(port),
        user=dbusr,
        password=dbpwd,
        db=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    init_mysql_db(trg_db)

if __name__ == '__main__':
    __main__()
