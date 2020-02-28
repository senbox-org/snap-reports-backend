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
    tests = support.get_test_list(branch=tag)
    res = __init_result__()
    for test in tests:
        stat = performances.get_status_dict(test, tag)
        if stat:
            res['count'] += 1
            improved = {'cpu': True, 'memory': True}
            for key in stat:
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
    tests = support.get_test_list(branch=tag)
    res = __init_result__()
    for test in tests:
        stat = performances.get_status_fulldata_dict(test, tag)
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
    tests = support.get_tests(branch=tag)
    res = []
    for test in tests:
        stat = performances.get_status_fulldata_dict(test['ID'], tag)
        if stat:
            stat['test'] = test
            res.append(stat)
    return json({'details': res})


@branch.route("/list")
async def get_list(_):
    """Get list of branches."""
    rows = DB.execute('SELECT ID, name FROM dockerTags;')
    res = []
    for row in rows:
        res.append(dict(row))
    return json({'branches': res})
