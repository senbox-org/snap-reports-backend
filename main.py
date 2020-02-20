"""
Simple backend for SNAP REPORT utility.
"""
import sqlite3
from sanic import Sanic
from sanic.response import json, text


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

APP = Sanic('SNAP Reports')
APP.config.from_pyfile('config')

DB = sqlite3.connect(APP.config.DB_FILE)
DB.row_factory = sqlite3.Row

TAGS = __init_tags__()
RESULTS = __init_results__()


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

@APP.route("/api/test")
async def test_list(request):
    """
    Retrieve list of tests.
    """
    query_str = ''
    for i, key in enumerate(request.args):
        if i > 0:
            query_str += " AND "
        val = request.args[key]
        query_str += f"{key}='{val[0]}'"

    if query_str:
        query_str = "WHERE " + query_str
    rows = DB.execute("SELECT * FROM tests "+query_str + " ORDER BY id")
    res = []
    for row in rows:
        res.append(dict(row))
    return json({"tests": res})

@APP.route("/api/test/<test_id:int>")
async def get_test(_, test_id):
    """
    Retrieve list of tests.
    """
    res = __get_test__(test_id)
    if res is None:
        return text("Test not found.", status=404)
    return json(res)

@APP.route("/api/test/<test_name:string>")
async def get_test_by_name(_, test_name):
    """
    Retrieve list of tests.
    """
    rows = DB.execute(f"SELECT * FROM tests where name='{test_name}'")
    res = None
    for row in rows:
        res = dict(row)
    if res is None:
        return text("Test not found.", status=404)
    return json(res)

@APP.route("/api/test/author/<name:string>")
async def get_test_by_author(_, name):
    """
    Retrieve list of tests.
    """
    rows = DB.execute(f"SELECT * FROM tests where author='{name}' ORDER BY id")
    res = []
    for row in rows:
        res.append(dict(row))
    return json({'tests':res})

@APP.route("/api/test/frequency/<name:string>")
async def get_test_by_frequency(_, name):
    """
    Retrieve list of tests.
    """
    rows = DB.execute(f"SELECT * FROM tests ORDER BY id")
    res = []
    lowcase = name.lower()
    for row in rows:
        val = dict(row)
        tag = val['frequency'].lower()
        if lowcase in tag:
            res.append(dict(row))
    return json({'tests':res})



@APP.route("/api/testset")
async def testset_list(_):
    """
    Retrieve list of testset.
    """
    rows = DB.execute("SELECT DISTINCT testset FROM tests")
    res = []
    for row in rows:
        res.append(row['testset'])
    return json({"testset": res})


@APP.route("/api/testset/<name:string>/tests")
async def testset_test_list(_, name):
    """
    Retrieve list of testset.
    """
    rows = DB.execute(f"SELECT * FROM tests WHERE testset='{name}' ORDER BY id")
    res = []
    for row in rows:
        res.append(dict(row))
    return json({"tests": res})

@APP.route("/api/job")
async def job_list(request):
    """
    Retrieve list of jobs.
    """
    query_str = ''
    for i, key in enumerate(request.args):
        if i > 0:
            query_str += " AND "
        val = request.args[key]
        query_str += f"{key}='{val[0]}'"

    if query_str:
        query_str = "WHERE " + query_str
    rows = DB.execute("SELECT * FROM jobs "+query_str + " ORDER BY id")
    res = []
    for row in rows:
        value = dict(row)
        value['dockerTag'] = __convert_tag__(value['dockerTag'])
        value['result'] = __convert_result__(value['result'])
        res.append(value)
    return json({"tests": res})

@APP.route("/api/job/tag/<tag:string>")
async def job_list_by_tag(_, tag):
    """
    Retrieve list of jobs.
    """
    tag = tag.lower()
    rows = DB.execute(f"SELECT * FROM jobs WHERE LOWER(testScope) = '{tag}' ORDER BY id")
    res = []
    for row in rows:
        value = dict(row)
        value['dockerTag'] = __convert_tag__(value['dockerTag'])
        value['result'] = __convert_result__(value['result'])
        res.append(value)
    return json({"tests": res})

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

@APP.route("/api/job/<job_id>")
async def get_job(_, job_id):
    """
    Retrieve list of jobs.

    Parameters:
    -----------
     - id: job id
    """
    job_id = __get_id__(job_id, 'jobs')
    if job_id is None:
        return text("Option non valid", status=500)
    res = __get_job__(job_id)
    if res is None:
        return text("Something bad happened", status=500)
    return json(res)


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

@APP.route("/api/job/<job_id>/statistics")
async def get_job_results(_, job_id):
    """
    Retrieve list of jobs.

    Parameters:
    -----------
     - id: job id
    """
    job_id = __get_id__(job_id, 'jobs')
    if job_id is None:
        return text("Option non valid", status=500)
    return __get_job_stats__(job_id)


@APP.route("/api/job/<job_id>/statistics/<exec_id:int>")
async def get_job_exec_stat(_, job_id, exec_id):
    """
    Retrieve list of jobs.

    Parameters:
    -----------
     - id: job id
    """
    job_id = __get_id__(job_id, 'jobs')

    if job_id is None:
        return text("Job option non valid", status=500)
    job = __get_job__(job_id)
    if job is None:
        return text("Job do not exist", status=404)

    rows = DB.execute(f"""
        SELECT *
        FROM results WHERE job = '{job_id}' AND id = '{exec_id}'""")
    res = None
    for row in rows:
        val = dict(row)
        val['result'] = __convert_result__(val['result'])
        val['test'] = __get_test__(val['test'])
        val['job'] = job
        res = val

    if not res:
        return text("No results found", status=404)
    return json(res)

@APP.route("/api/job/<job_id>/summary")
async def get_job_summary(_, job_id):
    """
    Retrieve list of jobs.

    Parameters:
    -----------
     - id: job id
    """
    job_id = __get_id__(job_id, 'jobs')
    if job_id is None:
        return text("Option not valid", status=500)
    job = __get_job__(job_id)
    if job is None:
        return text("Job do not exist", status=404)

    rows = DB.execute(f"""
        SELECT 
            result, duration, cpu_time, memory_avg, memory_max
        FROM results WHERE job = '{job_id}'""")
    summary = {
        'tests': 0,
        'duration': 0,
        'cpu_time': 0,
        'passed': 0,
        'failed': 0,
        'memory': {
            'max': 0,
            'average': 0,
        },
        'skipped': 0
    }

    for row in rows:
        summary['tests'] += 1
        summary['duration'] += row['duration']
        summary['cpu_time'] += row['cpu_time']
        if row['result'] == 1:
            summary['passed'] += 1
        elif row['result'] == 2:
            summary['skipped'] += 1
        else:
            summary['failed'] += 1
        if summary['memory']['max'] < row['memory_max']:
            summary['memory']['max'] = row['memory_max']
        summary['memory']['average'] += row['memory_avg']
    summary['memory']['average'] /= summary['tests']
    return json(summary)


if __name__ == "__main__":
    APP.run(host="0.0.0.0", port=APP.config.PORT)
