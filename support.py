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

def __get_test__(test_id):
    rows = DB.execute(f"SELECT * FROM tests where id='{test_id}'")
    res = None
    for row in rows:
        res = dict(row)
    return res

def __get_job__(job_id):
    rows = DB.execute(f"SELECT * FROM jobs WHERE id = '{job_id}'")
    res = None
    for row in rows:
        res = dict(row)
        res['dockerTag'] = __convert_tag__(res['dockerTag'])
        res['result'] = __convert_result__(res['result'])
    return res

def __convert_tag__(tag_id):
    return {
        "id": tag_id,
        "name": TAGS[tag_id]
    }

def __convert_result__(res_id):
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


def __get_id__(req, table):
    res_id = None
    if isinstance(req, int):
        res_id = req
    elif isinstance(req, str):
        low = req.lower()
        if low == 'last':
            res_id = __get_last_id__(table)
        if low == 'first':
            res_id = __get_first_id__(table)
    return res_id


def __get_job_stats__(job_id):
    job = __get_job__(job_id)
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
        val['result'] = __convert_result__(val['result'])
        val['test'] = __get_test__(val['test'])
        val['job'] = job
        res.append(val)

    if not res:
        return text("No results found", status=404)
    return json({'statistics':res})

TAGS = __init_tags__()
RESULTS = __init_results__()
