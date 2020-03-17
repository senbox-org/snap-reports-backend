"""
Simple interface for MySQL and SQLite DB.
"""
import sqlite3
import asyncio
import aiomysql
import time
import decimal


class SQLiteInterface:
    """SQLite Interface."""
    def __init__(self, dbname):
        self.connection = sqlite3.connect(dbname)
        self.connection.row_factory = sqlite3.Row

    async def execute(self, query, *args):
        """Execute query."""
        cursor = self.connection.cursor()
        cursor.execute(query, *args)
        self.connection.commit()
        cursor.close()

    async def fetchall(self, query, *args):
        """Fetch all rows of a query."""
        cursor = self.connection.cursor()
        res = cursor.execute(query, *args)
        rows = res.fetchall()
        self.connection.commit()
        cursor.close()
        return [dict(row) for row in rows]

    async def fetchone(self, query, *args):
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


def r2d(row, desc):
    """Convert row to dictionary."""
    if row is None:
        return None
    res = {}
    for i, col in enumerate(desc):
        key = str(col[0])
        res[key] = v2v(row[i])
    return res

def a2v(xs):
    """Convert array to value."""
    return [v2v(x) for x in xs]

def v2v(x):
    """Convert value to value."""
    if x is None:
        return None
    tx = type(x)
    if tx == list:
        return a2v(x)
    if tx == dict:
        return d2v(x)
    if tx == decimal.Decimal:
        return float(x)
    if tx == bytes:
        return x.decode('utf-8')
    if tx in (str, int, float):
        return x
    return str(x)


class MySQLInterfce:
    """MySQL interface."""
    def __init__(self, dbname):
        self.user, self.password = dbname.split('@')[0].split(':')
        self.db_name = dbname.split('@')[1].split('/')[1]
        self.host, self.port = dbname.split('@')[1].split('/')[0].split(':')
        self.port = int(self.port)
        self.connection = None

    async def open(self):
        loop = asyncio.get_event_loop()
        return await aiomysql.connect(host=self.host, port=self.port,
                                    user=self.user, password=self.password,
                                    db=self.db_name, loop=loop)

    async def execute(self, query, *args):
        """Execute query."""
        async with conn.cursor() as cursor:
            await cursor.execute(query, *args)

    async def fetchall(self, query, *args):
        """Fetch all rows of a query."""
        conn = await self.open()
        res = []   
        async with conn.cursor() as cursor:
            await cursor.execute(query, *args)
            desc = cursor.description
            rows = await cursor.fetchall()
            for row in rows:
                res.append(r2d(row, desc))        
        return res

    async def fetchone(self, query, *args):
        """Fetch one row of a query."""
        conn = await self.open()
        obj = None
        async with conn.cursor() as cursor:            
            await cursor.execute(query, *args)
            desc = cursor.description
            row = await cursor.fetchone()
            obj = r2d(row, desc)
        return obj

    def __del__(self):
        if self.connection:
            self.connection.close()


async def fetchone(cursor, query, *args):
    await cursor.execute(query, *args)
    desc = cursor.description
    row = await cursor.fetchone()
    obj = r2d(row, desc)
    return obj


async def fetchall(cursor, query, *args):
    await cursor.execute(query, *args)
    desc = cursor.description
    rows = await cursor.fetchall()
    res = []
    for row in rows:
        res.append(r2d(row, desc))        
    return res


async def execute(cursor, query, *args):
    await cursor.execute(query, *args)



def get_interface(mode, name):
    """Return correct DB interface given the current configuration."""
    mode = mode.upper()
    if mode == 'SQLITE':
        print('Deprcated')
        return None
    if mode == 'MYSQL':
        return MySQLInterfce(name)
    print(f'Mode `{mode}` not supported')
    return None
