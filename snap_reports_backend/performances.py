"""
Perforamnces and stats functions.

author: Martino Ferrari (CS Group)
email: martino.ferrari@c-s.fr
"""
import os
import numpy as np
from sanic.response import text, json

from datetime import datetime

from support import DB

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
                'average': np.mean(duration),
                'std': np.std(duration),
                'min': min(duration)
            },
            'cpu_time': {
                'average': np.mean(cpu_time),
                'std': np.std(cpu_time),
            },
            'cpu_usage': {
                'average': np.mean(cpu_usage),
                'std': np.std(cpu_usage),
            },
            'memory_avg': {
                'average': np.mean(memory),
                'std': np.std(memory),
                'max': max(memory_max)
            },
            'io_read': {
                'average': np.mean(io_read),
                'std': np.std(io_read),
                'min': min(io_read)
            },
            'io_write': {
                'average': np.mean(io_write),
                'std': np.std(io_write),
                'min': min(io_write)
            },
            'thread_num': {
                'average': np.mean(threads),
                'std': np.std(threads)
            }
        }
    return json(res)


def test_summary(test_id, tag=None):
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
    rows = DB.execute(query)
    rows = rows.fetchall()
    if not rows:
        return text("No rows found", status=500)
    return __parse_results__(rows)


def __get_test_name__(test_id):
    rows = DB.execute(f"""
        SELECT name
        FROM tests
        WHERE id = '{test_id}';
    """)
    row = rows.fetchone()
    if not row:
        return None
    return row[0]


def __get_reference__(test_id, field):
    rows = DB.execute(f"""
            SELECT {field}
            FROM reference_values
            WHERE test={test_id}
        """)
    row = rows.fetchone()
    if not row:
        return None
    return row[0]


def get_test_reference(test_id):
    """Get test references values."""
    rows = DB.execute(f"""
            SELECT
                updated, duration, cpu_time, cpu_usage_avg, memory_avg,
                memory_max, io_write, io_read, threads_avg
            FROM reference_values
            WHERE test={test_id}
        """)
    row = rows.fetchone()
    if not row:
        return None
    return dict(row)


def test_reference(test_id):
    """Get test references values."""
    if test_id is None:
        return text("Test not found", status=404)
    res = get_test_reference(test_id)
    if not res:
        return text("No reference found", status=404)
    return json(res)


def __history__(test_id, tag, field, last_n):
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
    rows = DB.execute(query)
    value = []
    date = []
    for row in rows:
        date.append(row['start'])
        value.append(row[field])
    return date, value


def __history_mean_value__(test_id, tag, field, last_n):
    _, value = __history__(test_id, tag, field, last_n)
    return np.mean(value)


def __history_moving_avg__(test_id, tag, field, last_n, window):
    date, value = __history__(test_id, tag, field, last_n)
    date = [datetime.fromisoformat(x).timestamp() for x in dates]
    sub_x = []
    sub_y = []
    for i in range(window, len(date)):
        sub_x.append(np.mean(date[i-window:i]))
        sub_y.append(np.mean(value[i-window:i]))
    return sub_x, sub_y


def history(test_id, tag, field, last_n=None):
    """Retrive the historic values of a specific field of a given test."""
    field = field.lower()
    if field not in FIELDS:
        return text("Field not valid", status=500)

    date, value = __history__(test_id, tag, field, last_n)
    return json({
        'date': date,
        'value': value
    })


def history_ma(test_id, tag, field, num, last_n=None):
    """Retrive the historic values of a specific field of a given test."""
    field = field.lower()
    if field not in FIELDS:
        return text("Field not valid", status=500)

    date, value = __history_moving_avg__(test_id, tag, field, last_n, num)
    return json({
        'date':  [datetime.fromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S') for x in dates],
        'value': value
    })


def get_status_fulldata_dict(test_id, tag):
    """Get branch test status."""
    ref_cpu_time = __get_reference__(test_id, "cpu_time")
    if ref_cpu_time is None:
        return None
    ref_memory = __get_reference__(test_id, "memory_avg")
    ref_read = __get_reference__(test_id, "io_read")
    _, cpu_time = __history__(test_id, tag, "cpu_time", None)
    if not len(cpu_time):
        return None
    _, memory = __history__(test_id, tag, "memory_avg", None)
    _, read = __history__(test_id, tag, 'io_read', None)
    res = {}
    res['cpu'] = {
        'last': cpu_time[0],
        'last10': np.mean(cpu_time[:10]),
        'average': np.mean(cpu_time),
        'reference': ref_cpu_time
    }
    res['memory'] = {
        'last': memory[0],
        'last10': np.mean(memory[:10]),
        'average': np.mean(memory),
        'reference': ref_memory
    }
    res['read'] = {
        'last': read[0],
        'last10': np.mean(read[:10]),
        'average': np.mean(read),
        'reference': ref_read
    }
    res['executions'] = len(cpu_time)
    return res


def get_status_dict(test_id, tag):
    """Get branch test status."""
    res = get_status_fulldata_dict(test_id, tag)
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


def get_status(test_id, tag):
    """Get branch test status."""
    res = get_status_dict(test_id, tag)
    if res is None:
        return text("No reference values found", status=500)
    return json(res)
