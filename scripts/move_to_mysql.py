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
        schema = schema_f.read().split(';')
        with connection.cursor() as cursor:
            for query in schema: 
                if query:
                    print(query)
                    cursor.execute(query)
        connection.commit()


def __val__(val):
    if isinstance(val, bytes):
        return "'"+val.decode('utf-8')+"'"
    return "'"+str(val)+"'"


def copy_table(table, source, target):
    with target.cursor() as cursor:
        print(f'== {table} ==')
        src_query = f'SELECT * FROM {table};'
        rows = source.execute(src_query)
        keys = None
        for i, row in enumerate(rows):
            if keys is None:
                keys = row.keys()
            print(f'\rRow {i+1:>6}', end='')
            query = f'INSERT INTO {table} ({", ".join(keys)}) '
            query += f"VALUES ({', '.join([__val__(row[key]) for key in keys])})"
            cursor.execute(query)
    print()
    target.commit()


def copy_db(source, target):
    copy_table('resultTags', source, target)
    copy_table('dockerTags', source, target)        
    copy_table('referenceTags', source, target)
    copy_table('tests', source, target)
    copy_table('jobs', source, target)
    copy_table('results', source, target)
    copy_table('reference_values', source, target)


def __main__():
    args = __args__()
    src_db = sqlite3.connect(args.source)
    src_db.row_factory = sqlite3.Row
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
    copy_db(src_db, trg_db)


if __name__ == '__main__':
    __main__()
