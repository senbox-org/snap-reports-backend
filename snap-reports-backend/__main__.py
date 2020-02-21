"""
Simple backend for SNAP REPORT utility.
"""
from sanic.response import json, text
from sanic import response
from support import APP, DB
import support
import performances

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
    rows = DB.execute("SELECT * FROM tests " + query_str + " ORDER BY id")
    res = []
    for row in rows:
        res.append(dict(row))
    return json({"tests": res})

@APP.route("/api/test/<test>")
async def get_test(_, test):
    """
    Retrieve test information.
    """
    test_id = support.get_test_id(test)
    if test_id is None:
        return text("Test not found", status=404)
    res = support.get_test(test_id)
    if res is None:
        return text("Test not found.", status=404)
    return json(res)

@APP.route("/api/test/<test>/summary")
async def get_test_summary(_, test):
    """
    Retrieve test performances summary.
    """
    test_id = support.get_test_id(test)
    if test_id is None:
        return text("Option not valid", status=500)
    return performances.test_summary(test_id)

@APP.route("/api/references")
async def get_references(_):
    """
    Retrieve list of references
    """
    rows = DB.execute("""
    SELECT
        id, test, referenceTag, updated, duration, cpu_time, cpu_usage_avg,
        cpu_usage_max, memory_avg, memory_max, io_write, io_read, threads_avg,
        threads_max
    FROM reference_values;""")
    res = []
    for row in rows:
        val = dict(row)
        val['test'] = support.get_test(val['test'])
        res.append(val)
    return json({'references': res})

@APP.route("/api/test/<test>/reference")
async def get_test_reference(_, test):
    """
    Retrieve test reference values.
    """
    test_id = support.get_test_id(test)
    if test_id is None:
        return text("Test not found", status=404)
    return performances.test_reference(test_id)

@APP.route("/api/test/<test>/history/<field:string>")
async def get_history(request, test, field):
    """
    Get history
    """
    test_id = support.get_test_id(test)
    if test_id is None:
        return text("Test not found", status=404)
    last_n = None
    if 'max' in request.args:
        last_n = int(request.args['max'][0])
    return performances.history(test_id, field, last_n)

@APP.route("/api/test/<test>/history/<field:string>/plot")
async def get_history_plot(request, test, field):
    test_id = support.get_test_id(test)
    if test_id is None:
        return text("Test not found", status=404)
    last_n = None
    if 'max' in request.args:
        last_n = int(request.args['max'][0])
    res = performances.history_plot(test_id, field, last_n)
    if res is None:
        return text("Field not found", status=404)
    return await response.file_stream(res)

@APP.route("/api/test/<test>/history/<field:string>/plot/moving_average")
async def get_history_plot(request, test, field):
    test_id = support.get_test_id(test)
    if test_id is None:
        return text("Test not found", status=404)
    last_n = None
    window = 5
    compare = False
    if 'window' in request.args:
        window = int(request.args['window'][0])
    if 'max' in request.args:
        last_n = int(request.args['max'][0])
    if 'compare' in request.args:
        compare = request.args['compare'][0].lower() == 'true'
    res = performances.history_plot_moving_average(test_id, field, window, last_n, compare)
    if res is None:
        return text("Field not found", status=404)
    return await response.file_stream(res)


@APP.route("/api/test/author/<name:string>")
async def get_test_by_author(_, name):
    """
    Retrieve list of tests by author.
    """
    rows = DB.execute(f"SELECT * FROM tests where author='{name}' ORDER BY id")
    res = []
    for row in rows:
        res.append(dict(row))
    return json({'tests':res})

@APP.route("/api/test/tag/<name:string>")
async def get_test_by_frequency(_, name):
    """
    Retrieve list of tests by frequency tag.
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


@APP.route("/api/testset/<name:string>")
async def testset_test_list(_, name):
    """
    Retrieve list of tests of a given testset.
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
        value['dockerTag'] = support.convert_tag(value['dockerTag'])
        value['result'] = support.convert_result(value['result'])
        res.append(value)
    return json({"tests": res})

@APP.route("/api/job/tag/<tag:string>")
async def job_list_by_tag(_, tag):
    """
    Retrieve list of job of a given frequency tag

    Parameters:
    -----------
     - tag: frequency tag
    """
    tag = tag.lower()
    rows = DB.execute(f"SELECT * FROM jobs WHERE LOWER(testScope) = '{tag}' ORDER BY id")
    res = []
    for row in rows:
        value = dict(row)
        value['dockerTag'] = support.convert_tag(value['dockerTag'])
        value['result'] = support.convert_result(value['result'])
        res.append(value)
    return json({"tests": res})


@APP.route("/api/job/<job_id>")
async def get_job(_, job_id):
    """
    Retrieve  job information.

    Parameters:
    -----------
     - id: job id
    """
    job_id = support.get_id(job_id, 'jobs')
    if job_id is None:
        return text("Option non valid", status=500)
    res = support.get_job(job_id)
    if res is None:
        return text("Something bad happened", status=500)
    return json(res)



@APP.route("/api/job/<job_id>/statistics")
async def get_job_results(_, job_id):
    """
    Retrieve job statistics.

    Parameters:
    -----------
     - job_id: job id
    """
    job_id = support.get_id(job_id, 'jobs')
    if job_id is None:
        return text("Option non valid", status=500)
    return support.get_job_stats(job_id)


@APP.route("/api/job/<job_id>/statistics/<exec_id:int>")
async def get_job_exec_stat(_, job_id, exec_id):
    """
    Retrieve list of jobs.

    Parameters:
    -----------
     - id: job id
    """
    job_id = support.get_id(job_id, 'jobs')

    if job_id is None:
        return text("Job option non valid", status=500)
    job = support.get_job(job_id)
    if job is None:
        return text("Job do not exist", status=404)

    rows = DB.execute(f"""
        SELECT *
        FROM results WHERE job = '{job_id}' AND id = '{exec_id}'""")
    res = None
    for row in rows:
        val = dict(row)
        val['result'] = support.convert_result(val['result'])
        val['test'] = support.get_test(val['test'])
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
    job_id = support.get_id(job_id, 'jobs')
    if job_id is None:
        return text("Option not valid", status=500)
    job = support.get_job(job_id)
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

@APP.route("/favicon.ico")
def favicon(_):
    """
    solve faviocon warnings
    """
    return text("NO ICON", status=404)


if __name__ == "__main__":
    APP.run(host="0.0.0.0", port=APP.config.PORT)
