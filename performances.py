"""
"""
import sys
import numpy as np
from support import DB
from sanic.response import text, json

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
            failed+= 1
    res = {
        'executions' : len(rows),
        'results' : {
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
        'memory': {
            'average': np.mean(memory),
            'std': np.std(memory),
            'max': max(memory_max)
        },
        'io_read': {
            'average': np.mean(io_read),
            'std': np.std(io_read),
            'min': min(io_read)
        },
        'io_wrtie': {
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


def test_summary(id):
    """
    Test summary.
    """
    if id is None:
        return text("Test not found", status=404)
    rows = DB.execute(f"""
    SELECT result, duration, cpu_time, cpu_usage_avg, memory_avg, memory_max, io_write, io_read, threads_avg
    FROM results
    WHERE test={id}
    """)
    rows = rows.fetchall()
    if not rows:
        return text("No rows found", status=500)
    return __parse_results__(rows)

def test_reference(id):
    """
    Test summary.
    """
    if id is None:
        return text("Test not found", status=404)
    rows = DB.execute(f"""
            SELECT updated, duration, cpu_time, cpu_usage_avg, memory_avg, memory_max, io_write, io_read, threads_avg
            FROM reference_values
            WHERE test={id}
        """)
    row = rows.fetchone()
    if not row:
        return text("No reference found", status=404)
    return json(dict(row))
