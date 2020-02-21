"""
Support file
"""
import sqlite3
from sanic import Sanic
from sanic.response import text, json


APP = Sanic('SNAP Reports')
APP.config.from_pyfile('config')

DB = sqlite3.connect(APP.config.DB_FILE)
DB.row_factory = sqlite3.Row

TAGS = []
RESULTS = []

def __init_tags__():
    rows = DB.execute("SELECT ID, name FROM dockerTags")
    res = {}
    for row in rows:
        res[row['id']] = row['name']
    return res

def __init_results__():
    rows = DB.execute("SELECT ID, tag FROM resultTags")
    res = {}
    for row in rows:
        res[row['id']] = row['tag']
    return res

def get_test(test_id):
    rows = DB.execute(f"SELECT * FROM tests where id='{test_id}'")
    res = None
    for row in rows:
        res = dict(row)
    return res

def get_job(job_id):
    rows = DB.execute(f"SELECT * FROM jobs WHERE id = '{job_id}'")
    res = None
    for row in rows:
        res = dict(row)
        res['dockerTag'] = convert_tag(res['dockerTag'])
        res['result'] = convert_result(res['result'])
    return res

def convert_tag(tag_id):
    return {
        "id": tag_id,
        "name": TAGS[tag_id]
    }

def convert_result(res_id):
    return {
        "id": res_id,
        "tag": RESULTS[res_id]
    }

def __get_last_id__(table):
    rows = DB.execute(f"SELECT max(id) FROM {table}")
    return rows.fetchone()[0]

def __get_first_id__(table):
    rows = DB.execute(f"SELECT min(id) FROM {table}")
    return rows.fetchone()[0]


def get_id(req, table):
    res_id = None
    if isinstance(req, int):
        res_id = req
        print("HERE")
    elif isinstance(req, str):
        low = req.lower()
        if low == 'last':
            res_id = __get_last_id__(table)
        if low == 'first':
            res_id = __get_first_id__(table)
        if req.isdigit():
            res_id = int(req)
    return res_id

def get_test_id(test):
    if isinstance(test, int):
        return test
    if isinstance(test, str):
        if test.isdigit():
            return int(test)
        if test.lower() == 'last':
            return __get_last_id__('tests')
        if test.lower() == 'first':
            return __get_first_id__('tests')
        rows = DB.execute(f"SELECT id FROM tests where name='{test}'")
        res = None
        for row in rows:
            res = row['id']
        return res
    return None

def get_job_stats(job_id):
    job = get_job(job_id)
    if job is None:
        return text("Job do not exist", status=404)

    rows = DB.execute(f"""
        SELECT
            id, test, job, result, start, duration, cpu_time, cpu_usage_avg,
            cpu_usage_max, memory_avg, memory_max, io_write, io_read, threads_avg
        FROM results WHERE job = '{job_id}' ORDER BY id""")
    res = []
    for row in rows:
        val = dict(row)
        val['result'] = convert_result(val['result'])
        val['test'] = get_test(val['test'])
        val['job'] = job
        res.append(val)

    if not res:
        return text("No results found", status=404)
    return json({'statistics':res})

TAGS = __init_tags__()
RESULTS = __init_results__()
