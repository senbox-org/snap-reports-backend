"""Implement api/branch apis."""
from sanic import Blueprint
from sanic.response import json, text

import support
import performances
from support import DB
import dbfactory


branch = Blueprint('api_branch', url_prefix='/branch')

FIELD_SET = ('cpu_time', 'memory_avg', 'memory_max', 'duration', 'io_read', 'io_write')


def __init_result__():
    return {
        "count": 0,
        "improved": {
            'duration': 0,
            'cpu': 0,
            'memory': 0,
            'read': 0,
            'both': 0,
        },
        "duration": {
            "last": 0,
            "last10": 0,
            "average": 0,
        },
        "cpu": {
            "last": 0,
            "last10": 0,
            "average": 0,
        },
        "memory": {
            "last": 0,
            "last10": 0,
            "average": 0,
        },
        "read": {
            "last": 0,
            "last10": 0,
            "average": 0,
        }
    }

async def __stats_N__(cursor, tag, last=None):
    query = f"""
    SELECT 
        COUNT(results.ID), 
        AVG((reference_values.duration - results.duration)/ reference_values.duration * 100), 
        AVG((reference_values.cpu_time - results.cpu_time)/ reference_values.cpu_time * 100), 
        AVG((reference_values.memory_avg - results.memory_avg)/reference_values.memory_avg * 100), 
        AVG((reference_values.io_read - results.io_read) / reference_values.io_read * 100),
        SUM(reference_values.duration * 0.97 > results.duration),
        SUM(reference_values.cpu_time * 0.97 > results.cpu_time),
        SUM(reference_values.memory_avg * 0.97 > results.memory_avg),
        SUM(reference_values.io_read * 0.97 > results.io_read),
        SUM(reference_values.io_read * 0.97 > results.io_read AND 
            reference_values.memory_avg * 0.97 > results.memory_avg AND
            reference_values.duration * 0.97 > results.duration),
        SUM(reference_values.duration * 1.03 < results.duration),
        SUM(reference_values.cpu_time * 1.03 < results.cpu_time),
        SUM(reference_values.memory_avg * 1.03 < results.memory_avg),
        SUM(reference_values.io_read * 1.03 < results.io_read),
        SUM(reference_values.io_read  * 1.03 < results.io_read AND 
            reference_values.memory_avg * 1.03 < results.memory_avg AND
            reference_values.duration  * 1.03 < results.duration)
    FROM results 
    JOIN (
            SELECT ID from jobs where 
            dockerTag = 
                (SELECT ID from dockerTags WHERE name='{tag}')
            ORDER BY ID DESC {'LIMIT '+str(last) if last else ''}
        ) jobs ON results.job IN (jobs.ID)
    INNER JOIN resultTags ON
        results.result = resultTags.ID
    INNER JOIN reference_values ON
        results.test = reference_values.test
    WHERE 
        resultTags.tag = "SUCCESS";
    """
    row = await dbfactory.fetchone(cursor, query)
    values = list(row.values()) 
    return {
        'count': values[0],
        'duration': values[1],
        'cpu': values[2],
        'memory': values[3],
        'read': values[4],
        'improved': {
            'duration': values[5],
            'cpu': values[6],
            'memory': values[7],
            'read': values[8],
            'both': values[9] 
        },
        'regressed': {
            'duration': values[10],
            'cpu': values[11],
            'memory': values[12],
            'read': values[13],
            'both': values[14] 
        }
    }


def parse_tag(tag):
    """Function to decode url tag"""
    return tag.replace('%3A', ':')

@branch.route("/<tag:str>/summary")
async def get_branch_summary(_, tag):
    """Get branch statistics summary."""
    tag = parse_tag(tag)
    conn = await DB.open()
    async with conn.cursor() as cursor:
        res = __init_result__()
        
        data = {
            'last': await __stats_N__(cursor, tag, 1),
            'last10': await __stats_N__(cursor, tag, 10),
            'average': await __stats_N__(cursor, tag, None),
        }
        res['count'] = data['last10']['count']
        res['improved'] = data['last10']['improved']
        res['regressed'] = data['last10']['regressed']

        for key in ('duration', 'cpu', 'memory', 'read'):
            res[key] = {
                'last': data['last'][key],
                'last10': data['last10'][key],
                'average': data['average'][key]
            }

        return json(res)


@branch.route("/<tag:str>/summary/absolute")
async def get_branch_summary_absolute(_, tag):
    """Get branch statistics absolute numbers."""
    tag = parse_tag(tag)
    tests = await support.get_test_list(branch=tag)
    res = __init_result__()
    for test in tests:
        stat = await performances.get_status_fulldata_dict(test, tag)
        if stat:
            res['count'] += 1
            for key in stat:
                for sub_key in stat[key]:
                    if sub_key in res[key]:
                        value = (stat[key][sub_key] - stat[key]['reference'])
                        res[key][sub_key] += value
    return json(res)


@branch.route("/<tag:str>/history/scheduled/<field:str>")
async def get_branch_schduled_field_history(_, tag, field):
    result = await performances.get_branch_scheduled_field_history(tag, field) 
    if  result is None:
        return text(f"Field `{field}` does not exist", status=500)
    dates, values = result
    return json({"date": dates, "value": values})


@branch.route("/<tag:str>/history/scheduled/<field:str>/<window:int>")
async def get_branch_scheduled_field_history_ma(_, tag, field, window):
    tag = parse_tag(tag)
    result = await performances.get_branch_scheduled_field_history_moving_average(tag, field, window) 
    if  result is None:
        return text(f"Field `{field}` does not exist", status=500)
    dates, values = result
    return json({"date": dates, "value": values})


@branch.route("/<tag:str>/history/<field:str>")
async def get_branch_field_history(_, tag, field):
    tag = parse_tag(tag)
    result = await performances.get_branch_field_history(tag, field) 
    if  result is None:
        return text(f"Field `{field}` does not exist", status=500)
    dates, values = result
    return json({"date": dates, "value": values})

@branch.route("/<tag:str>/history/<field:str>/<window:int>")
async def get_branch_field_history_ma(_, tag, field, window):
    tag = parse_tag(tag)
    result = await performances.get_branch_field_history_moving_average(tag, field, window) 
    if  result is None:
        return text(f"Field `{field}` does not exist", status=500)
    dates, values = result
    return json({"date": dates, "value": values})


async def __details_N__(tag, num):
    query = f"""
    SELECT 
        tests.ID AS test_ID, 
        tests.name AS test_name, 
        COUNT(results.ID) AS num_exec, 
        AVG(results.duration) AS res_duration,  
        AVG(results.cpu_time) AS res_cpu,
        AVG(results.memory_avg) AS res_memory, 
        AVG(results.io_read) AS res_read, 
        AVG(reference_values.duration) AS ref_duration, 
        AVG(reference_values.cpu_time) AS ref_cpu,
        AVG(reference_values.memory_avg) AS ref_memory, 
        AVG(reference_values.io_read) AS ref_read
    FROM results 
    JOIN (
        SELECT ID from jobs where 
        dockerTag = 
            (SELECT ID from dockerTags WHERE name='{tag}')
        ORDER BY ID DESC {'LIMIT '+str(num) if num else ''}
    ) jobs on results.job In (jobs.ID)
    INNER JOIN reference_values ON
        results.test = reference_values.test
    INNER JOIN tests ON
        results.test = tests.ID
    INNER JOIN resultTags ON
        results.result = resultTags.ID
    WHERE 
        resultTags.tag = 'SUCCESS'
    GROUP BY tests.ID;
    """
    stats = await DB.fetchall(query)
    return stats


@branch.route("/<tag:str>/details/last")
async def get_branch_details_last(_, tag):
    """Get branch statistics summary."""
    tag = parse_tag(tag)
    query = f"""
    SELECT 
        tests.ID AS test_ID, tests.name AS name, 
        results.ID AS result_ID, results.job, resultTags.tag AS result, 
        results.start, results.duration / ref.duration AS duration, 
        results.cpu_time / ref.cpu_time AS cpu_time,
        results.memory_avg / ref.memory_avg AS memory_avg, 
        results.memory_max / ref.memory_max AS memory_max, 
        results.io_read / ref.io_read AS io_read, 
        results.io_write / ref.io_write AS io_write
    FROM tests
    INNER JOIN reference_values AS ref ON ref.test = tests.ID
    INNER JOIN results ON results.test = tests.ID
    JOIN (
            SELECT test, max(job) AS lastJob 
            FROM results 
            WHERE job IN
                (SELECT ID FROM jobs WHERE dockerTag = (SELECT ID FROM dockerTags WHERE name = '{tag}')) 
            GROUP BY test
        ) filtr ON filtr.test = results.test AND filtr.lastJob = results.job
    INNER JOIN resultTags ON results.result = resultTags.ID
    ORDER BY tests.ID;
    """
    stats = await DB.fetchall(query)
    return json(stats)

@branch.route("/<tag:str>/details")
async def get_branch_details_n(_, tag):
    """Get branch statistics summary."""
    return json({'details': await __details_N__(tag, None)})

@branch.route("/<tag:str>/details/<n:int>")
async def get_branch_details(_, tag, n):
    """Get branch statistics summary."""
    return json({'details': await __details_N__(tag, n)})


@branch.route("/<tag:str>/last_job")
async def get_branch_last_job(_, tag):
    """Get last job of a given branch."""
    tag = parse_tag(tag)
    row = await DB.fetchone(f'''
        SELECT jobs.ID, jobs.jobnum, jobs.timestamp_start, jobs.testScope, 
            resultTags.tag
        FROM jobs
        INNER JOIN resultTags ON jobs.result = resultTags.ID
        WHERE jobs.dockerTag =
            (SELECT ID FROM dockerTags WHERE name='{tag}')
        ORDER BY jobs.ID DESC LIMIT 1;''')
    return json(row)


@branch.route("/list")
async def get_list(_):
    """Get list of branches."""
    rows = await DB.fetchall('SELECT ID, name FROM dockerTags;')
    return json({'branches': rows})


@branch.route("/<tag:str>/njobs")
async def get_branch_njobs(_, tag):
    """Get number of jobs executed of a given branch."""
    tag = parse_tag(tag)
    row = await DB.fetchone(f'''
        SELECT COUNT(ID) 
        FROM jobs
        WHERE dockerTag = (
            SELECT ID 
            FROM dockerTags
            WHERE name='{tag}'
        );''')
    return json({'njobs': row['COUNT(ID)']})


@branch.route("/compare/<tag_a:str>/<tag_b:str>/<field:str>")
async def get_branch_comparison(request, tag_a, tag_b, field):
    """
    Compare a specific field of two different branches

    Parameters
    ----------
     - request: request argument
     - tag_a: first branch tag
     - tag_b: second branch tag
     - field: field to examine (CPU Time, Memory etc)
    """
    tag_a = parse_tag(tag_a)
    tag_b = parse_tag(tag_b)
    if field.lower() not in FIELD_SET:
        return text(f"Field `{field}` does not exist", status=500)
    q_filter = ''
    for key in request.args:
        value = request.args[key][0]
        if key == 'author':
            q_filter += f" AND UPPER(tests.{key}) = '{value.upper()}'"
        else:
            q_filter += f" AND tests.{key} LIKE '%{value}%'"
    
    intersect_query = f"""
    SELECT
    DISTINCT results.test
    FROM results
    INNER JOIN jobs ON jobs.ID = results.job
    WHERE 
        jobs.dockerTag = (SELECT ID FROM dockerTags WHERE name='{tag_a}')
        AND
        results.result = (SELECT ID FROM resultTags WHERE tag='SUCCESS')
        AND
        results.test in  (
            SELECT DISTINCT
            results.test
            FROM results
            INNER JOIN jobs ON jobs.ID = results.job
            WHERE 
                jobs.dockerTag = (SELECT ID FROM dockerTags WHERE name='{tag_b}')
                AND
                results.result = (SELECT ID FROM resultTags WHERE tag='SUCCESS'))
    """

    query_a = f"""
    SELECT 
        tests.ID AS test_ID, 
        tests.name AS test_name, 
        COUNT(results.ID) AS num_exec, 
        AVG(results.{field.lower()}) AS field
    FROM results 
    JOIN (
        SELECT ID from jobs where 
        dockerTag = 
            (SELECT ID from dockerTags WHERE name='{tag_a}')
        ORDER BY jobs.timestamp_start DESC LIMIT 5
    ) jobs on results.job In (jobs.ID)
    INNER JOIN tests ON
        results.test = tests.ID
    INNER JOIN resultTags ON
        results.result = resultTags.ID
    WHERE 
        resultTags.tag = 'SUCCESS'
    AND 
        tests.ID in ({intersect_query})
    {q_filter}
    GROUP BY tests.ID
    ORDER BY tests.ID ASC;
    """

    query_b = f"""
    SELECT 
        tests.ID AS test_ID, 
        tests.name AS test_name, 
        COUNT(results.ID) AS num_exec, 
        AVG(results.{field.lower()}) AS field
    FROM results 
    JOIN (
        SELECT ID from jobs where 
        dockerTag = 
            (SELECT ID from dockerTags WHERE name='{tag_b}')
        ORDER BY jobs.timestamp_start DESC LIMIT 5
    ) jobs on results.job In (jobs.ID)
    INNER JOIN tests ON
        results.test = tests.ID
    INNER JOIN resultTags ON
        results.result = resultTags.ID
    WHERE 
        resultTags.tag = 'SUCCESS'
    AND 
        tests.ID in ({intersect_query})
    {q_filter}
    GROUP BY tests.ID
    ORDER BY tests.ID ASC;
    """
    stats_a = await DB.fetchall(query_a)
    stats_b = await DB.fetchall(query_b)
    results = []
    search = lambda lst, test_id: [i for i, el in enumerate(lst) if el['test_ID'] == test_id][0]
    for el_a in stats_a:
        id_b = search(stats_b, el_a['test_ID'])
        el_b = stats_b[id_b]
        stats_b.pop(id_b)
        val = {
            'test_ID': el_a['test_ID'],
            'test_name': el_a['test_name'],
            'br_a_count': el_a['num_exec'],
            'br_b_count': el_b['num_exec'],
            'br_a_avg': el_a['field'],
            'br_b_avg': el_b['field'],
            'diff_abs': el_a['field'] - el_b['field'],
            'diff_rel': (el_a['field'] - el_b['field']) / el_b['field'] * 100
        }
        results.append(val)
    return json(results)