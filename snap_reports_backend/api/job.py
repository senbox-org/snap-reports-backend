"""Implement api/job apis."""
from sanic import Blueprint
from sanic.response import json, text

import csv

from support import DB
import support
import performances

job = Blueprint('api_job', url_prefix='/job')


def __convert_csv__(data):
    string = data
    reader = csv.reader(string.splitlines()[2:], delimiter=',')
    rows = []
    for row in reader:
        rows.append(row)
    return rows


@job.route("/list")
async def job_list(request):
    """Retrieve list of jobs."""
    query_str = ''
    for i, key in enumerate(request.args):
        if i > 0:
            query_str += " AND "
        val = request.args[key]
        query_str += f"{key}='{val[0]}'"

    if query_str:
        query_str = "WHERE " + query_str
    rows = await DB.fetchall("SELECT * FROM jobs "+query_str + " ORDER BY id DESC")

    for value in rows:
        value['dockerTag'] = await support.convert_tag(value['dockerTag'])
        value['result'] = await support.convert_result(value['result'])
    return json(rows)


@job.route("/tag/<tag:str>")
async def job_list_by_tag(_, tag):
    """
    Retrieve list of job of a given frequency tag.

    Parameters:
    -----------
     - tag: frequency tag
    """
    tag = tag.lower()
    rows = await DB.fetchall(
        f"SELECT * FROM jobs WHERE LOWER(testScope) = '{tag}' ORDER BY id")
    res = []
    for row in rows:
        value = row
        value['dockerTag'] = await support.convert_tag(value['dockerTag'])
        value['result'] = await support.convert_result(value['result'])
        res.append(value)
    return json({"tests": res})


@job.route("/<job_id>")
async def get_job(_, job_id):
    """
    Retrieve  job information.

    Parameters:
    -----------
     - id: job id
    """
    job_id = await support.get_id(job_id, 'jobs')
    if job_id is None:
        return text("Option non valid", status=500)
    res = await support.get_job(job_id)
    
    if res is None:
        return text("Something bad happened", status=500)
    return json(res)
    

@job.route("/<job_id>/statistics")
async def get_job_results(_, job_id):
    """
    Retrieve job statistics.

    Parameters:
    -----------
     - job_id: job id
    """
    job_id = await support.get_id(job_id, 'jobs')
    if job_id is None:
        return text("Option non valid", status=500)
    return await support.get_job_stats(job_id)


@job.route("/<job_id>/statistics/<exec_id:int>")
async def get_job_exec_stat(_, job_id, exec_id):
    """
    Retrieve list of jobs.

    Parameters:
    -----------
     - id: job id
    """
    job_id = await support.get_id(job_id, 'jobs')

    if job_id is None:
        return text("Job option non valid", status=500)
    job_obj = await support.get_job(job_id)
    if job_obj is None:
        return text("Job do not exist", status=404)

    val = await DB.fetchone(f"""
        SELECT *
        FROM results WHERE job = '{job_id}' AND test = '{exec_id}'""")
    if val:
        val['result'] = await support.convert_result(val['result'])
        val['test'] = await support.get_test(val['test'])
        val['job'] = job_obj
        val['raw_data'] = __convert_csv__(val['raw_data'])
        return json(val)
    return text("No results found", status=404)


@job.route("/<job_id>/summary")
async def get_job_summary(_, job_id):
    """
    Retrieve list of jobs.

    Parameters:
    -----------
     - id: job id
    """
    job_id = await support.get_id(job_id, 'jobs')
    if job_id is None:
        return text("Option not valid", status=500)
    job_obj = await support.get_job(job_id)
    if job_obj is None:
        return text("Job do not exist", status=404)

    rows = await DB.fetchall(f"""
        SELECT
            test, result, duration, cpu_time, memory_avg, memory_max, io_read,
            io_write
        FROM results WHERE job = '{job_id}' ORDER BY test""")

    summary = {
        'num_tests': 0,
        'duration': 0,
        'cpu_time': 0,
        'passed': 0,
        'failed': 0,
        'memory': {
            'max': 0,
            'average': 0,
        },
        'IO': {
            'read': 0,
            'write': 0,
        },
        'tests': [],
        'skipped': 0
    }
    if not rows:
        return summary

    for row in rows:
        test_id = row['test']
        reference = await performances.get_test_reference(test_id)
        if reference:
            test = {
                'duration': row['duration'] / reference['duration'],
                'cpu_time': row['cpu_time'] / reference['cpu_time'],
                'memory': {
                    'average': row['memory_avg'] / reference['memory_avg'],
                    'max': row['memory_max'] / reference['memory_max']
                },
                'IO': {
                    'read': row['io_read'] / reference['io_read'],
                    'write': row['io_write'] / reference['io_write']
                }
            }
        else:
            test = {}
        test['name'] = await performances.__get_test_name__(test_id)
        test['ID'] = row['test']
        summary['tests'].append(test)
        summary['num_tests'] += 1
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
        summary['IO']['read'] += row['io_read']
        summary['IO']['write'] += row['io_write']
        summary['memory']['average'] += row['memory_avg']
    summary['memory']['average'] /= summary['num_tests']
    return json(summary)


@job.route("/<job_id>/summary/testsets")
async def get_testsets_summary(_, job_id):
    """Get testset summary."""
    job_id = await support.get_id(job_id, 'jobs')
    if job_id is None:
        return text("Option not valid", status=500)
    job_obj = await support.get_job(job_id)
    if job_obj is None:
        return text("Job do not exist", status=404)

    rows = await DB.fetchall(f"""
        SELECT
            tests.ID AS tst_ID, 
            tests.name AS tst_name,
            tests.testset AS tst_testset, 
            results.result AS res_ID, 
            resultTags.tag AS res_tag, 
            results.duration AS prf_duration, 
            results.cpu_time AS prf_cpu_time, 
            results.memory_avg AS prf_memory_avg, 
            results.memory_max AS prf_memory_max, 
            results.io_read AS prf_io_read,
            results.io_write AS prf_io_write, 
            reference_values.updated AS ref_updated,
            reference_values.duration AS ref_duration, 
            reference_values.cpu_time AS ref_cpu_time, 
            reference_values.memory_avg AS ref_memory_avg, 
            reference_values.memory_max AS ref_memory_max, 
            reference_values.io_read AS ref_io_read,
            reference_values.io_write AS ref_io_write,
            reference_values.threads_avg as ref_threads_avg
        FROM results 
        LEFT JOIN reference_values ON reference_values.test = results.test
        INNER JOIN tests ON 
            results.test = tests.ID
        INNER JOIN resultTags ON
            results.result = resultTags.ID
        WHERE job = {job_id}
        ORDER BY tests.ID""")
    passed = 0
    count = 0
    summary = {}
    for row in rows:
        testset = row['tst_testset']
        count += 1
        if testset not in summary:
            summary[testset] = []
        summ = {
            'ID': row['tst_ID'],
            'name': row['tst_name'],
            'result': {
                'ID': row['res_ID'],
                'tag': row['res_tag']
            },
            'profile': {
                'duration': row['prf_duration'],
                'cpu_time': row['prf_cpu_time'],
                'memory_max': row['prf_memory_max'],
                'memory_avg': row['prf_memory_avg'],
                'io_read': row['prf_io_read'],
                'io_write': row['prf_io_write'],
            },
            'reference': None if row['ref_duration'] is None else {
                'updated': row['ref_updated'],
                'duration': row['ref_duration'],
                'cpu_time': row['ref_cpu_time'],
                'memory_max': row['ref_memory_max'],
                'memory_avg': row['ref_memory_avg'],
                'io_read': row['ref_io_read'],
                'io_write': row['ref_io_write'],
                'threads_avg': row['ref_threads_avg']
            }
        }
        if summ['result']['tag'] == 'SUCCESS':
            passed += 1
        summary[testset].append(summ)

    return json({
        'num_tests': count,
        'passed': passed,
        'testsets': summary
    })
