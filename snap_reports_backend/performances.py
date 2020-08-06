"""
Perforamnces and stats functions.

author: Martino Ferrari (CS Group)
email: martino.ferrari@c-s.fr
"""
import os
import statistics
from sanic.response import text, json

from datetime import datetime

from support import DB
import dbfactory

CWD = os.path.abspath(os.getcwd())


FIELDS = ["duration", "cpu_time", "cpu_usage_avg", "cpu_usage_max",
          "memory_avg", "memory_max", "io_read", "io_write", "threads_avg",
          "threads_max"]


def __parse_results__(rows):
    duration = []
    cpu_time = []
    cpu_usage = []
    memory = []
    memory_max = []
    io_read = []
    io_write = []
    threads = []
    passed = 0
    skipped = 0
    failed = 0
    for row in rows:
        if row['result'] == 1:
            passed += 1
            duration.append(row['duration'])
            cpu_time.append(row['cpu_time'])
            cpu_usage.append(row['cpu_usage_avg'])
            memory.append(row['memory_avg'])
            memory_max.append(row['memory_max'])
            io_read.append(row['io_read'])
            io_write.append(row['io_write'])
            threads.append(row['threads_avg'])
        elif row['result'] == 2:
            skipped += 1
        else:
            failed += 1

    res = {'executions': 0, 'results': {'passed': 0, 'skipped': 0, 'failed': 0}}
    if len(duration) > 0:
        res = {
            'executions': len(rows),
            'results': {
                'passed': passed,
                'skipped': skipped,
                'failed': failed
            },
            'duration': {
                'average': statistics.mean(duration),
                'std': statistics.stdev(duration),
                'min': min(duration)
            },
            'cpu_time': {
                'average': statistics.mean(cpu_time),
                'std': statistics.stdev(cpu_time),
            },
            'cpu_usage': {
                'average': statistics.mean(cpu_usage),
                'std': statistics.stdev(cpu_usage),
            },
            'memory_avg': {
                'average': statistics.mean(memory),
                'std': statistics.stdev(memory),
                'max': max(memory_max)
            },
            'io_read': {
                'average': statistics.mean(io_read),
                'std': statistics.stdev(io_read),
                'min': min(io_read)
            },
            'io_write': {
                'average': statistics.mean(io_write),
                'std': statistics.stdev(io_write),
                'min': min(io_write)
            },
            'thread_num': {
                'average': statistics.mean(threads),
                'std': statistics.stdev(threads)
            }
        }
    return json(res)


async def test_summary(test_id, tag=None):
    """Get test summary."""
    if test_id is None:
        return text("Test not found", status=404)
    query = f"""
    SELECT
        result, duration, cpu_time, cpu_usage_avg, memory_avg, memory_max,
        io_write, io_read, threads_avg
    FROM results
    WHERE test={test_id}
    """
    if tag is not None:
        query += f"""
        AND job IN
            (SELECT ID FROM jobs WHERE dockerTag =
                (SELECT ID FROM dockerTags WHERE name='snap:{tag}'));"""
    rows = await DB.fetchall(query)
    if not rows:
        return text("No rows found", status=500)
    return __parse_results__(rows)


async def __get_test_name__(test_id):
    row = await DB.fetchone(f"""
        SELECT name
        FROM tests
        WHERE id = '{test_id}';
    """)
    if not row:
        return None
    return row['name']


async def __get_reference__(test_id, field, cursor=None):
    query = f"""
            SELECT {field}
            FROM reference_values
            WHERE test={test_id}
        """
    if cursor:
        row = await dbfactory.fetchone(cursor, query)
    else:
        row = await DB.fetchone(query)
    if not row:
        return None
    return row[field]


async def get_test_reference(test_id):
    """Get test references values."""
    row = await DB.fetchone(f"""
            SELECT
                updated, duration, cpu_time, cpu_usage_avg, memory_avg,
                memory_max, io_write, io_read, threads_avg
            FROM reference_values
            WHERE test={test_id}
        """)
    return row


async def test_reference(test_id):
    """Get test references values."""
    if test_id is None:
        return text("Test not found", status=404)
    res = await get_test_reference(test_id)
    if not res:
        return text("No reference found", status=404)
    return json(res)


async def __history__(test_id, tag, field, last_n, cursor=None):
    if tag.lower() != 'any':
        query = f"""
            SELECT start, {field}
            FROM results
            WHERE test = '{test_id}' AND result = '1'
            AND job IN (SELECT id FROM jobs WHERE dockerTag =
                (SELECT id FROM dockerTags WHERE name='snap:{tag}'))
            ORDER BY start DESC
            """
    else:
        query = f"""
            SELECT start, {field}
            FROM results
            WHERE test = '{test_id}' AND result = '1'
            ORDER BY start DESC
            """
    if last_n is not None:
        query += f" LIMIT {last_n}"
    if cursor:
        rows = await dbfactory.fetchall(cursor, query)
    else:
        rows = await DB.fetchall(query)
    value = []
    date = []
    for row in rows:
        date.append(row['start'])
        value.append(row[field])
    return date, value


async def __history_mean_value__(test_id, tag, field, last_n):
    _, value = await __history__(test_id, tag, field, last_n)
    return statistics.mean(value)


async def __history_moving_avg__(test_id, tag, field, last_n, window):
    date, value = await __history__(test_id, tag, field, last_n)
    date = [datetime.fromisoformat(x).timestamp() for x in date]
    sub_x = []
    sub_y = []
    for i in range(window, len(date)):
        sub_x.append(statistics.mean(date[i-window:i]))
        sub_y.append(statistics.mean(value[i-window:i]))
    return sub_x, sub_y


async def history(test_id, tag, field, last_n=None, cursor=None):
    """Retrive the historic values of a specific field of a given test."""
    field = field.lower()
    if field not in FIELDS:
        return text("Field not valid", status=500)

    date, value = await __history__(test_id, tag, field, last_n, cursor=cursor)
    return json({
        'date': date,
        'value': value
    })


async def history_ma(test_id, tag, field, num, last_n=None):
    """Retrive the historic values of a specific field of a given test."""
    field = field.lower()
    if field not in FIELDS:
        return text("Field not valid", status=500)

    date, value = await __history_moving_avg__(test_id, tag, field, last_n, num)
    return json({
        'date':  [datetime.fromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S') for x in date],
        'value': value
    })


async def get_status_fulldata_dict(test_id, tag, cursor=None):
    """Get branch test status."""
    ref_cpu_time = await __get_reference__(test_id, "cpu_time", cursor=cursor)
    if ref_cpu_time is None:
        return None
    ref_memory = await __get_reference__(test_id, "memory_avg", cursor=cursor)
    ref_read = await __get_reference__(test_id, "io_read", cursor=cursor)
    _, cpu_time = await __history__(test_id, tag, "cpu_time", last_n=None, cursor=cursor)
    if not len(cpu_time):
        return None
    _, memory = await __history__(test_id, tag, "memory_avg", last_n=None, cursor=cursor)
    _, read = await __history__(test_id, tag, 'io_read', last_n=None, cursor=cursor)
    res = {}
    res['cpu'] = {
        'last': cpu_time[0],
        'last10': statistics.mean(cpu_time[:10]),
        'average': statistics.mean(cpu_time),
        'reference': ref_cpu_time
    }
    res['memory'] = {
        'last': memory[0],
        'last10': statistics.mean(memory[:10]),
        'average': statistics.mean(memory),
        'reference': ref_memory
    }
    res['read'] = {
        'last': read[0],
        'last10': statistics.mean(read[:10]),
        'average': statistics.mean(read),
        'reference': ref_read
    }
    res['executions'] = len(cpu_time)
    return res


async def get_status_dict(test_id, tag, cursor=None):
    """Get branch test status."""
    res = await get_status_fulldata_dict(test_id, tag, cursor=cursor)
    if not res:
        return None
    for key in res:
        if isinstance(res[key], dict):
            ref = res[key]['reference']
            for subkey in res[key]:
                if subkey != 'reference':
                    val = res[key][subkey]
                    res[key][subkey] = (1 - val/ref) * 100
    return res


async def get_status(test_id, tag):
    """Get branch test status."""
    res = await get_status_dict(test_id, tag)
    if res is None:
        return text("No reference values found", status=500)
    return json(res)


async def get_branch_scheduled_field_history(tag, field):
    """Get history of a field for a branch, realative to reference."""
    if field not in FIELDS:
        return None
    query = f"""
    SELECT jobs.timestamp_start AS time, (100 - 100 * AVG(results.{field})/AVG(reference_values.{field})) AS value
    FROM results
    INNER JOIN reference_values ON reference_values.test = results.test
    INNER JOIN jobs ON jobs.ID = results.job
    WHERE jobs.dockerTag = (SELECT ID FROM dockerTags WHERE name='snap:{tag}') 
        AND results.result = (SELECT ID FROM resultTags WHERE tag='SUCCESS')
        AND (jobs.testScope = 'DAILY' OR jobs.testScope = 'WEEKLY') 
    GROUP BY jobs.ID
    ORDER BY jobs.timestamp_start DESC;
    """
    stats = await DB.fetchall(query)
    timestamp = [x['time'] for x in stats]
    values = [x['value'] for x in stats]
    return timestamp, values


async def get_branch_scheduled_field_history_moving_average(tag, field, window):
    res = await get_branch_scheduled_field_history(tag, field)
    if res is None:
        return None
    dates, values = res
    dates = [datetime.fromisoformat(x).timestamp() for x in dates]
    sub_x = []
    sub_y = []
    for i in range(window, len(dates)):
        sub_x.append(statistics.mean(dates[i-window:i]))
        sub_y.append(statistics.mean(values[i-window:i]))
    sub_x = [datetime.fromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S') for x in sub_x]
    return sub_x, sub_y


async def get_branch_field_history(tag, field):
    """Get history of a field for a branch, realative to reference."""
    if field not in FIELDS:
        return None
    query = f"""
    SELECT jobs.timestamp_start AS time, (100 - 100 * AVG(results.{field})/AVG(reference_values.{field})) AS value
    FROM results
    INNER JOIN reference_values ON reference_values.test = results.test
    INNER JOIN jobs ON jobs.ID = results.job
    WHERE jobs.dockerTag = (SELECT ID FROM dockerTags WHERE name='snap:{tag}') 
        AND results.result = (SELECT ID FROM resultTags WHERE tag='SUCCESS')
    GROUP BY jobs.ID
    ORDER BY jobs.timestamp_start DESC;
    """
    stats = await DB.fetchall(query)
    timestamp = [x['time'] for x in stats]
    values = [x['value'] for x in stats]
    return timestamp, values

async def get_branch_field_history_moving_average(tag, field, window):
    res = await get_branch_field_history(tag, field)
    if res is None:
        return None
    dates, values = res
    dates = [datetime.fromisoformat(x).timestamp() for x in dates]
    sub_x = []
    sub_y = []
    for i in range(window, len(dates)):
        sub_x.append(statistics.mean(dates[i-window:i]))
        sub_y.append(statistics.mean(values[i-window:i]))
    sub_x = [datetime.fromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S') for x in sub_x]
    return sub_x, sub_y