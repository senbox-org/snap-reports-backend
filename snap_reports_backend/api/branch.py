"""Implement api/branch apis."""
from sanic import Blueprint
from sanic.response import json

import support
import performances
from support import DB

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


@branch.route("/<tag:string>/summary")
async def get_branch_summary(_, tag):
    """Get branch statistics summary."""
    tests = await support.get_test_list(branch=tag)
    res = __init_result__()
    for test in tests:
        stat = await performances.get_status_dict(test, tag)
        if stat:
            res['count'] += 1
            improved = {'cpu': True, 'memory': True}
            for key in stat:
                if isinstance(stat[key], dict):
                    for sub_key in stat[key]:
                        if sub_key == 'last10' and stat[key][sub_key] < 0:
                            improved[key] = False
                        if sub_key in res[key]:
                            res[key][sub_key] += stat[key][sub_key]
            for key in improved:
                if improved[key]:
                    res['improved'][key] += 1
            if all(improved.values()):
                res['improved']['both'] += 1
    if res['count']:
        for key in res['cpu']:
            res['cpu'][key] /= res['count']
        for key in res['memory']:
            res['memory'][key] /= res['count']
        for key in res['read']:
            res['read'][key] /= res['count']
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
