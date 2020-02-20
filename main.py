"""
Simple backend for SNAP REPORT utility.
"""
from sanic.response import json, text
from support import APP, DB
import support




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
    res = support.__get_test__(test_id)
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
        value['dockerTag'] = support.__convert_tag__(value['dockerTag'])
        value['result'] = support.__convert_result__(value['result'])
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
        value['dockerTag'] = support.__convert_tag__(value['dockerTag'])
        value['result'] = support.__convert_result__(value['result'])
        res.append(value)
    return json({"tests": res})


@APP.route("/api/job/<job_id>")
async def get_job(_, job_id):
    """
    Retrieve list of jobs.

    Parameters:
    -----------
     - id: job id
    """
    job_id = support.__get_id__(job_id, 'jobs')
    if job_id is None:
        return text("Option non valid", status=500)
    res = support.__get_job__(job_id)
    if res is None:
        return text("Something bad happened", status=500)
    return json(res)




@APP.route("/api/job/<job_id>/statistics")
async def get_job_results(_, job_id):
    """
    Retrieve list of jobs.

    Parameters:
    -----------
     - id: job id
    """
    job_id = support.__get_id__(job_id, 'jobs')
    if job_id is None:
        return text("Option non valid", status=500)
    return support.__get_job_stats__(job_id)


@APP.route("/api/job/<job_id>/statistics/<exec_id:int>")
async def get_job_exec_stat(_, job_id, exec_id):
    """
    Retrieve list of jobs.

    Parameters:
    -----------
     - id: job id
    """
    job_id = support.__get_id__(job_id, 'jobs')

    if job_id is None:
        return text("Job option non valid", status=500)
    job = support.__get_job__(job_id)
    if job is None:
        return text("Job do not exist", status=404)

    rows = DB.execute(f"""
        SELECT *
        FROM results WHERE job = '{job_id}' AND id = '{exec_id}'""")
    res = None
    for row in rows:
        val = dict(row)
        val['result'] = support.__convert_result__(val['result'])
        val['test'] = support.__get_test__(val['test'])
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
    job_id = support.__get_id__(job_id, 'jobs')
    if job_id is None:
        return text("Option not valid", status=500)
    job = support.__get_job__(job_id)
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
