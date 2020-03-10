"""
Simple interface for MySQL and SQLite DB.
"""
import sqlite3
import pymysql


class SQLiteInterface:
    """SQLite Interface."""
    def __init__(self, dbname):
        self.connection = sqlite3.connect(dbname)
        self.connection.row_factory = sqlite3.Row

    def execute(self, query, *args):
        """Execute query."""
        cursor = self.connection.cursor()
        cursor.execute(query, *args)
        self.connection.commit()
        cursor.close()

    def fetchall(self, query, *args):
        """Fetch all rows of a query."""
        cursor = self.connection.cursor()
        res = cursor.execute(query, *args)
        rows = res.fetchall()
        self.connection.commit()
        cursor.close()
        return [dict(row) for row in rows]

    def fetchone(self, query, *args):
        """Fetch one row of a query."""
        cursor = self.connection.cursor()
        res = cursor.execute(query, *args)
        row = res.fetchone()
        self.connection.commit()
        cursor.close()
        return dict(row)

    def close(self):
        """Close connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def __del__(self):
        self.close()


class MySQLInterfce:
    """MySQL interface."""
    def __init__(self, dbname):
        dbusr, dbpwd = dbname.split('@')[0].split(':')
        db_name = dbname.split('@')[1].split('/')[1]
        host, port = dbname.split('@')[1].split('/')[0].split(':')
        self.connection = pymysql.connect(
            host=host,
            port=int(port),
            user=dbusr,
            password=dbpwd,
            db=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )

    def execute(self, query, *args):
        """Execute query."""
        with self.connection.cursor() as cursor:
            cursor.execute(query, *args)
        self.connection.commit()

    def fetchall(self, query, *args):
        """Fetch all rows of a query."""
        with self.connection.cursor() as cursor:
            cursor.execute(query, *args)
            rows = cursor.fetchall()
        self.connection.commit()
        return rows

    def fetchone(self, query, *args):
        """Fetch one row of a query."""
        with self.connection.cursor() as cursor:
            cursor.execute(query, *args)
            row = cursor.fetchone()
        self.connection.commit()
        return row

    def close(self):
        """Close connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def __del__(self):
        self.close()

def get_interface(mode, name):
    """Return correct DB interface given the current configuration."""
    mode = mode.upper()
    if mode == 'SQLITE':
        return  SQLiteInterface(name)
    if mode == 'MYSQL':
        return MySQLInterfce(name)
    print(f'Mode `{mode}` not supported')
    return None
