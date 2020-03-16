"""Implement api/test apis."""
from sanic import Blueprint
from sanic.response import json, text

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
    rows = await DB.fetchall("SELECT * FROM tests " + query_str + " ORDER BY id")
    res = []
    for row in rows:
        res.append(dict(row))
    return json({"tests": res})


@test.route("/<test>")
async def get_test(_, test):
    """Retrieve test information."""
    test_id = await support.get_test_id(test)
    if test_id is None:
        return text(f"Test `{test}` not found", status=404)
    res = await support.get_test(test_id)
    if res is None:
        return text(f"Test `{test}` not found", status=404)
    return json(res)


@test.route("/<test>/summary")
async def get_test_summary(_, test):
    """Retrieve test performances summary."""
    test_id = await support.get_test_id(test)
    if test_id is None:
        return text(f"Test `{test}` not found", status=404)
    return await performances.test_summary(test_id)


@test.route("/<test>/summary/<tag:string>")
async def get_test_summary_by_tag(_, test, tag):
    """Retrieve test performances summary."""
    test_id = await support.get_test_id(test)
    if test_id is None:
        return text(f"Test `{test}` not found", status=404)
    return await performances.test_summary(test_id, tag)


@test.route("/api/test/<test>/status/<tag:string>")
async def get_test_status(_, test, tag):
    """Get status of a test in of a specific branch."""
    test_id = await support.get_test_id(test)
    if test_id is None:
        return text(f"Test `{test}` not found", status=404)
    return await performances.get_status(test_id, tag)


@test.route("/<test>/reference")
async def get_test_reference(_, test):
    """Retrieve test reference values."""
    test_id = await support.get_test_id(test)
    if test_id is None:
        return text("Test not found", status=404)
    return await performances.test_reference(test_id)


@test.route("/<test>/history/<field:string>/<tag:string>")
async def get_history(request, test, field, tag):
    """Get history."""
    test_id = await support.get_test_id(test)
    if test_id is None:
        return text("Test not found", status=404)
    last_n = None
    if 'max' in request.args:
        last_n = int(request.args['max'][0])
    return await performances.history(test_id, tag, field, last_n)


@test.route("/<test>/moving_average/<field:string>/<tag:string>/<num:int>")
async def get_history_moving_avg(request, test, field, tag, num):
    """Get history."""
    test_id = await support.get_test_id(test)
    if test_id is None:
        return text("Test not found", status=404)
    last_n = None
    if 'max' in request.args:
        last_n = int(request.args['max'][0])
    return await performances.history_ma(test_id, tag, field, num, last_n)


@test.route("/author/<name:string>")
async def get_test_by_author(_, name):
    """Retrieve list of tests by author."""
    res = await DB.fetchall(f"SELECT * FROM tests where author='{name}' ORDER BY id")
    return json({'tests': res})


@test.route("/tag/<name:string>")
async def get_test_by_frequency(_, name):
    """Retrieve list of tests by frequency tag."""
    rows = await DB.fetchall(f"SELECT * FROM tests ORDER BY id")
    res = []
    lowcase = name.lower()
    for val in rows:
        tag = val['frequency'].lower()
        if lowcase in tag:
            res.append(val)
    return json({'tests': res})


@test.route('/<tag>/count')
async def get_test_exec_count(_, tag):
    """Get number of execution of a given test."""
    test_id = await support.get_test_id(tag)
    if test_id is None:
        return text(f"Test `{tag}` not found", status=404)
    row = await DB.fetchone(f'''
        SELECT COUNT(ID)
        FROM jobs
        WHERE ID IN
            (SELECT job FROM results WHERE test = '{test_id}');
        ''')
    return json({'count': row[0]})


@test.route('/<tag>/last_job')
async def get_test_last_job(_, tag):
    """Get last job of a given test."""
    test_id = await support.get_test_id(tag)
    if test_id is None:
        return text(f"Test `{tag}` not found", status=404)
    row = await DB.fetchone(f'''
        SELECT jobs.*, resultTags.tag, dockerTags.name
        FROM jobs 
        INNER JOIN resultTags ON jobs.result = resultTags.ID
        INNER JOIN dockerTags ON jobs.dockerTag = dockerTags.ID
        WHERE jobs.ID IN 
            (SELECT job FROM results WHERE test = '{test_id}')
        ORDER BY jobs.ID DESC LIMIT 1;
        ''')
    return json(row)
