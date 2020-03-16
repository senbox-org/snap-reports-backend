"""Implement api/branch apis."""
from sanic import Blueprint
from sanic.response import json

import support
import performances
from support import DB
import dbfactory


branch = Blueprint('api_branch', url_prefix='/branch')


def __init_result__():
    return {
        "count": 0,
        "improved": {
            'cpu': 0,
            'memory': 0,
            'read': 0,
            'both': 0,
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

async def __stats_N__(cursor, tag, field, last=None):
    query = f"""
    SELECT AVG({field})
    From results 
    Join (
        SELECT ID from jobs where 
        dockerTag = 
            (SELECT ID from dockerTags WHERE name='snap:{tag}')
        ORDER BY ID DESC {'LIMIT '+str(last) if last else ''}
    ) jobs ON job IN (jobs.ID)
    WHERE 
        test in (select test from reference_values);
    """

    res = await dbfactory.fetchone(cursor, query)
    avg = res[f'AVG({field})']

    query = f"""
    SELECT AVG(reference_values.{field})
    From reference_values
    inner Join results on reference_values.test = results.test
    Join (
        SELECT ID from jobs where 
        dockerTag = 
            (SELECT ID from dockerTags WHERE name='snap:{tag}')
        ORDER BY ID DESC {'LIMIT '+str(last) if last else ''}
    ) jobs on results.job In (jobs.ID);
    """
    res = await dbfactory.fetchone(cursor, query)
    ref = res[f'AVG(reference_values.{field})']
    return float(avg) / float(ref) * 100

async def __stats__(cursor, tag, field):
    return {
        'last': await __stats_N__(cursor, tag, field, 1),
        'last10': await __stats_N__(cursor, tag, field, 10),
        'average': await __stats_N__(cursor, tag, field, None)
    }

async def __improved__(cursor, tag, *fields):
    query = f'''
    SELECT COUNT(results.ID) 
    From results 
    Join (
        SELECT ID from jobs where 
        dockerTag = 
            (SELECT ID from dockerTags WHERE name='snap:{tag}')
        ORDER BY ID DESC LIMIT 10
    ) jobs on results.job In (jobs.ID);
    '''
    row = await dbfactory.fetchone(cursor, query)
    count = row['COUNT(results.ID)']
    query = f'''
    SELECT COUNT(results.ID) 
    From results 
    Join (
        SELECT ID from jobs where 
        dockerTag = 
            (SELECT ID from dockerTags WHERE name='snap:{tag}')
        ORDER BY ID DESC LIMIT 10
    ) jobs on results.job In (jobs.ID)
    INNER JOIN reference_values ON results.test = reference_values.test
    WHERE 
    '''
    query += ' AND '.join([f'results.{field} < reference_values.{field}' for field in fields])
    row = await dbfactory.fetchone(cursor, query)
    improved = row['COUNT(results.ID)']
    return int(improved) / int(count) * 100


@branch.route("/<tag:string>/summary")
async def get_branch_summary(_, tag):
    """Get branch statistics summary."""
    conn = await DB.open()
    async with conn.cursor() as cursor:
        res = __init_result__()
        row = await dbfactory.fetchone(cursor, f"""
            SELECT COUNT(ID)
            From results 
            WHERE job in 
                (SELECT ID 
                 FROM jobs 
                 WHERE dockerTag = 
                    (SELECT ID from dockerTags WHERE name='snap:{tag}')
                ) 
            AND test in (select test from reference_values);""")
        res['count'] = row['COUNT(ID)']

        for key, field in [('cpu', 'cpu_time'), ('memory', 'memory_avg'), ('read', 'io_read')]:
            res[key] = await __stats__(cursor, tag, field)
            res['improved'][key] = await __improved__(cursor, tag, field)
        res['improved']['both'] = await __improved__(cursor, tag, 'cpu_time', 'memory_avg', 'io_read')

        return json(res)


@branch.route("/<tag:string>/summary/absolute")
async def get_branch_summary_absolute(_, tag):
    """Get branch statistics absolute numbers."""
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


@branch.route("/<tag:string>/details")
async def get_branch_details(_, tag):
    """Get branch statistics summary."""
    tests = await support.get_tests(branch=tag)
    res = []
    for test in tests:
        stat = await performances.get_status_fulldata_dict(test['ID'], tag)
        if stat:
            stat['test'] = test
            res.append(stat)
    return json({'details': res})


@branch.route("/<tag:string>/last_job")
async def get_branch_last_job(_, tag):
    """Get last job of a given branch."""
    row = await DB.fetchone(f'''
        SELECT jobs.ID, jobs.jobnum, jobs.timestamp_start, jobs.testScope, 
            resultTags.tag
        FROM jobs
        INNER JOIN resultTags ON jobs.result = resultTags.ID
        WHERE jobs.dockerTag =
            (SELECT ID FROM dockerTags WHERE name='snap:{tag}')
        ORDER BY jobs.ID DESC LIMIT 1;''')
    return json(row)


@branch.route("/list")
async def get_list(_):
    """Get list of branches."""
    rows = await DB.fetchall('SELECT ID, name FROM dockerTags;')
    return json({'branches': rows})


@branch.route("/<tag:string>/njobs")
async def get_branch_njobs(_, tag):
    """Get number of jobs executed of a given branch."""
    row = await DB.fetchone(f'''
        SELECT COUNT(ID) 
        FROM jobs
        WHERE dockerTag = (
            SELECT ID 
            FROM dockerTags
            WHERE name='snap:{tag}'
        );''')
    return json({'njobs': row['COUNT(ID)']})
