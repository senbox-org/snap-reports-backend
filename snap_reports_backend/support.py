"""Support functions and utilities."""
import sys
import os
from sanic import Sanic
from sanic.response import text, json
from sanic_cors import CORS
import dbfactory
import uvloop
import asyncio

# setup event loop policy
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# initialization of DB and server app.
if len(sys.argv) < 2:
    print("Missing configuration file")
    sys.exit(1)

APP = Sanic('SNAP Reports')
CORS(APP)
CFG_FILE = sys.argv[1]

if os.path.exists(CFG_FILE+'.local'):
    CFG_FILE += '.local'

APP.config.from_pyfile(CFG_FILE)

DB = dbfactory.get_interface(APP.config.DB_MODE, APP.config.DB)

if not DB:
    sys.exit(1)

TAGS = {}
RESULTS = {}


async def __tag__(id):
    return await DB.fetchone(f"SELECT ID, name FROM dockerTags WHERE ID='{id}'")


async def __result__(id):
    return await DB.fetchone(f"SELECT ID, tag FROM resultTags WHERE ID='{id}'")


async def get_test(test_id):
    """
    Retrieve test information.

    Parameters:
    -----------
     -  test_id : db test id
    """
    row = await DB.fetchone(f"SELECT * FROM tests where id='{test_id}'")
    return row


async def get_job(job_id):
    """
    Retrieve job inforation.

    Paramters:
    ----------
     - job_id: db job id
    """
    res = await DB.fetchone(f"SELECT * FROM jobs WHERE id = '{job_id}'")
    res['dockerTag'] = await convert_tag(res['dockerTag'])
    res['result'] = await convert_result(res['result'])
    return res


async def convert_tag(tag_id):
    """
    Convert dockerTag:id to dockerTag object.

    Parameters:
    -----------
     - tag_id: tag name
    """
    global TAGS
    if tag_id in TAGS:
        return TAGS[tag_id]
    value = await __tag__(tag_id)
    TAGS[tag_id] = value
    return value

async def convert_result(res_id):
    """Convert result:id to result object."""
    global RESULTS
    if res_id in RESULTS:
        return RESULTS[res_id]
    value = await __result__(res_id)
    RESULTS[res_id] = value
    return value

async def __get_last_id__(table):
    res = await DB.fetchone(f"SELECT max(id) FROM {table}")
    return res['max(id)']


async def __get_first_id__(table):
    res = await DB.fetchone(f"SELECT min(id) FROM {table}")
    return res['min(id)']


async def get_id(req, table):
    """
    Convert request ids to real DB id of a given table.

    In particular it supports `first` and `last` keyword.
    """
    res_id = None
    if isinstance(req, int):
        res_id = req
    elif isinstance(req, str):
        low = req.lower()
        if low == 'last':
            res_id = await __get_last_id__(table)
        if low == 'first': 
            res_id = await __get_first_id__(table)
        if req.isdigit():
            res_id = int(req)
    return res_id


async def get_test_id(test):
    """
    Expand get_id function for test table.

    It adds the possibility to retrieve the test information from the test
    name.
    """
    if isinstance(test, int):
        return test
    if isinstance(test, str):
        if test.isdigit():
            return int(test)
        if test.lower() == 'last':
            return __get_last_id__('tests')
        if test.lower() == 'first':
            return __get_first_id__('tests')
        row = await DB.fetchone(f"SELECT ID FROM tests where name='{test}'")
        if row:
            return row['ID']
    return None


async def get_job_stats(job_id):
    """Get job statistics."""
    job = await get_job(job_id)
    if job is None:
        return text("Job do not exist", status=404)

    rows = await DB.fetchall(f"""
        SELECT
            ID, test, job, result, start, duration, cpu_time, cpu_usage_avg,
            cpu_usage_max, memory_avg, memory_max, io_write, io_read,
            threads_avg
        FROM results WHERE job = '{job_id}' ORDER BY ID""")
    res = []
    for row in rows:
        val = row
        val['result'] = await convert_result(val['result'])
        val['test'] = await get_test(val['test'])
        val['job'] = job
        res.append(val)

    if not res:
        return text("No results found", status=404)
    return json({'statistics': res})


async def get_test_list(cursor=None, branch=None):
    """Get test list."""
    query = "SELECT test FROM results WHERE"
    if branch:
        query += f""" job IN (SELECT ID FROM jobs WHERE dockerTag = (
            SELECT ID FROM dockerTags WHERE name = 'snap:{branch}'
        ))"""
    query += " GROUP BY test"
    if cursor:
        rows = await dbfactory.fetchall(cursor, query)
    else:
        rows = await DB.fetchall(query)
    return [row['test'] for row in rows]


async def get_tests(branch=None):
    """Get full tests."""
    query = """SELECT * FROM tests WHERE ID IN
        (SELECT DISTINCT test FROM results WHERE
    """
    if branch:
        query += f""" job IN (SELECT ID FROM jobs WHERE dockerTag = (
            SELECT ID FROM dockerTags WHERE name = 'snap:{branch}'
        ))"""
    query += ") ORDER BY ID"
    return await DB.fetchall(query)

