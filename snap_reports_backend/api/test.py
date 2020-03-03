"""Implement api/test apis."""
from sanic import Blueprint
from sanic.response import json, text, file_stream

from support import DB
import support
import performances

test = Blueprint('api_test', url_prefix='/test')


@test.route("/list")
async def test_list(request):
    """Retrieve list of tests."""
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


@test.route("/<test>")
async def get_test(_, test):
    """Retrieve test information."""
    test_id = support.get_test_id(test)
    if test_id is None:
        return text(f"Test `{test}` not found", status=404)
    res = support.get_test(test_id)
    if res is None:
        return text(f"Test `{test}` not found", status=404)
    return json(res)


@test.route("/<test>/summary")
async def get_test_summary(_, test):
    """Retrieve test performances summary."""
    test_id = support.get_test_id(test)
    if test_id is None:
        return text(f"Test `{test}` not found", status=404)
    return performances.test_summary(test_id)


@test.route("/<test>/summary/<tag:string>")
async def get_test_summary_by_tag(_, test, tag):
    """Retrieve test performances summary."""
    test_id = support.get_test_id(test)
    if test_id is None:
        return text(f"Test `{test}` not found", status=404)
    return performances.test_summary(test_id, tag)


@test.route("/api/test/<test>/status/<tag:string>")
async def get_test_status(_, test, tag):
    """Get status of a test in of a specific branch."""
    test_id = support.get_test_id(test)
    if test_id is None:
        return text(f"Test `{test}` not found", status=404)
    return performances.get_status(test_id, tag)


@test.route("/<test>/reference")
async def get_test_reference(_, test):
    """Retrieve test reference values."""
    test_id = support.get_test_id(test)
    if test_id is None:
        return text("Test not found", status=404)
    return performances.test_reference(test_id)


@test.route("/<test>/history/<field:string>/<tag:string>")
async def get_history(request, test, field, tag):
    """Get history."""
    test_id = support.get_test_id(test)
    if test_id is None:
        return text("Test not found", status=404)
    last_n = None
    if 'max' in request.args:
        last_n = int(request.args['max'][0])
    return performances.history(test_id, tag, field, last_n)


@test.route("/<test>/moving_average/<field:string>/<tag:string>/<num:int>")
async def get_history_moving_avg(request, test, field, tag, num):
    """Get history."""
    test_id = support.get_test_id(test)
    if test_id is None:
        return text("Test not found", status=404)
    last_n = None
    if 'max' in request.args:
        last_n = int(request.args['max'][0])
    return performances.history_ma(test_id, tag, field, num, last_n)


@test.route("/<test>/history/<field:string>/plot/<tag:string>")
async def get_history_plot(request, test, field, tag):
    """Return history plot."""
    test_id = support.get_test_id(test)
    if test_id is None:
        return text("Test not found", status=404)
    last_n = None
    if 'max' in request.args:
        last_n = int(request.args['max'][0])
    res = performances.history_plot(test_id, tag, field, last_n)
    if res is None:
        return text("Field not found", status=404)
    return await file_stream(res)


@test.route("/<test>/history/<field:string>/plot/relative/<tag:string>/" +
            "<reference:string>")
async def get_relative_plot(request, test, field, tag, reference):
    """Return relative plot."""
    test_id = support.get_test_id(test)
    if test_id is None:
        return text("Test not found", status=404)
    last_n = None
    if 'max' in request.args:
        last_n = int(request.args['max'][0])
    res = performances.relative_plot(test_id, tag, reference, field, last_n)
    if res is None:
        return text("Field not found", status=404)
    return await file_stream(res)


async def __moving_average_plot__(request, test, field, tag, num=10, rel=None):
    test_id = support.get_test_id(test)
    if test_id is None:
        return text("Test not found", status=404)
    last_n = None
    window = num
    compare = False
    if 'max' in request.args:
        last_n = int(request.args['max'][0])
    if rel is None:
        if 'compare' in request.args:
            compare = request.args['compare'][0].lower() == 'true'
        res = performances.history_plot_moving_average(test_id, tag, field,
                                                       window, last_n, compare)
    else:
        res = performances.relative_plot(test_id, tag, rel, field, last_n,
                                         window)
    if res is None:
        return text("Field not found", status=404)
    return await file_stream(res)


@test.route("/<test>/history/<field:string>/plot/relative/<tag:string>/" +
            "<reference:string>/<num:int>")
async def get_relative_plot_moving(request, test, field, tag, reference, num):
    """Return relative plot."""
    return await __moving_average_plot__(request, test, field, tag, num,
                                         reference)


@test.route("/<test>/history/<field:string>/plot/moving_average/" +
            "<tag:string>/<num:int>")
async def get_history_moving_avg_plot(request, test, field, tag, num):
    """Return moving average plot."""
    return await __moving_average_plot__(request, test, field, tag, num=num)


@test.route("/<test>/history/<field:string>/plot/moving_average/<tag:string>")
async def get_history_moving_avg_plot_default(request, test, field, tag):
    """Plot history moving average with default value."""
    return await __moving_average_plot__(request, test, field, tag)


@test.route("/author/<name:string>")
async def get_test_by_author(_, name):
    """Retrieve list of tests by author."""
    rows = DB.execute(f"SELECT * FROM tests where author='{name}' ORDER BY id")
    res = []
    for row in rows:
        res.append(dict(row))
    return json({'tests': res})


@test.route("/tag/<name:string>")
async def get_test_by_frequency(_, name):
    """Retrieve list of tests by frequency tag."""
    rows = DB.execute(f"SELECT * FROM tests ORDER BY id")
    res = []
    lowcase = name.lower()
    for row in rows:
        val = dict(row)
        tag = val['frequency'].lower()
        if lowcase in tag:
            res.append(dict(row))
    return json({'tests': res})


@test.route('/<tag>/count')
async def get_test_exec_count(_, tag):
    """Get number of execution of a given test."""
    test_id = support.get_test_id(tag)
    if test_id is None:
        return text(f"Test `{tag}` not found", status=404)
    rows = DB.execute(f'''
        SELECT COUNT(ID)
        FROM jobs
        WHERE ID IN
            (SELECT job FROM results WHERE test = '{test_id}');
        ''')
    row = rows.fetchone()
    return json({'count': row[0]})


@test.route('/<tag>/last_job')
async def get_test_last_job(_, tag):
    """Get last job of a given test."""
    test_id = support.get_test_id(tag)
    if test_id is None:
        return text(f"Test `{tag}` not found", status=404)
    rows = DB.execute(f'''
        SELECT jobs.*, resultTags.tag, dockerTags.name
        FROM jobs 
        INNER JOIN resultTags ON jobs.result = resultTags.ID
        INNER JOIN dockerTags ON jobs.dockerTag = dockerTags.ID
        WHERE jobs.ID IN 
            (SELECT job FROM results WHERE test = '{test_id}')
        ORDER BY jobs.ID DESC LIMIT 1;
        ''')
    row = rows.fetchone()
    return json(dict(row))
