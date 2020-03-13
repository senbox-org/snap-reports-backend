"""
Simple interface for MySQL and SQLite DB.
"""
import sqlite3
import pymysql
import time


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


def r2d(row):
    """Convert row to dictionary."""
    val = {}
    for key in row:
        val[str(key)] = row[key]
    return row 


class MySQLInterfce:
    """MySQL interface."""
    def __init__(self, dbname):
        self.dbusr, self.dbpwd = dbname.split('@')[0].split(':')
        self.db_name = dbname.split('@')[1].split('/')[1]
        self.host, self.port = dbname.split('@')[1].split('/')[0].split(':')
        self.connection = None
        self.__open__()

    def __open__(self):
        print('Connecting to DB', end='', flush=True)
        while True:
            print('.', end='', flush=True)
            try:
                connection = pymysql.connect(
                    host=self.host,
                    port=int(self.port),
                    user=self.dbusr,
                    password=self.dbpwd,
                    db=self.db_name,
                    cursorclass=pymysql.cursors.DictCursor
                )
                if connection.open:
                    self.connection = connection
                    print("[DONE]")
                    return True
                time.sleep(5)
            except pymysql.err.OperationalError:
                time.sleep(5)

    def is_connected(self):
        """Check MySQL connection."""
        return self.connection and self.connection.open

    def execute(self, query, *args):
        """Execute query."""
        if self.is_connected():
            with self.connection.cursor() as cursor:
                cursor.execute(query, *args)
            self.connection.commit()

    def fetchall(self, query, *args):
        """Fetch all rows of a query."""
        if self.is_connected():
            rows = []
            with self.connection.cursor() as cursor:
                cursor.execute(query, *args)
                rows = cursor.fetchall()
            self.connection.commit()
            return [r2d(row) for row in rows]
        return []

    def fetchone(self, query, *args):
        """Fetch one row of a query."""
        if self.is_connected():
            row = None
            with self.connection.cursor() as cursor:
                cursor.execute(query, *args)
                row = cursor.fetchone()
            self.connection.commit()
            return r2d(row)
        return None

    def close(self):
        """Close connection."""
        if self.is_connected():
            self.connection.close()

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
