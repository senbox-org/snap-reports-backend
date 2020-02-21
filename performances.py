"""
"""
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from support import DB
from sanic.response import text, json
import os

CWD = os.path.abspath(os.getcwd())
PLT_PATH = os.path.join(CWD,'plots')

if not os.path.isdir(PLT_PATH):
    os.mkdir(PLT_PATH)

FIELDS = ["duration", "cpu_time", "cpu_usage_avg", "cpu_usage_max", "memory_avg", 
    "memory_max", "io_read", "io_write", "threads_avg", "threads_max"]

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


def __history__(test_id, field, last_n):
    query = f"""
        SELECT start, {field} 
        FROM results 
        WHERE test = '{test_id}' AND result = '1'
        ORDER BY start DESC
        """
    if last_n is not None:
        query += f" LIMIT {last_n}"
    rows = DB.execute(query)
    value =[]
    date = []
    for row in rows:
        date.append(row['start'])
        value.append(row[field])
    return date, value

def history(test_id, field, last_n=None):
    field = field.lower()
    if field not in FIELDS:
        return text("Field not valid", status=500)
   
    date, value = __history__(test_id, field, last_n)
    return json({
        'date': date,
        'value': value
    })


def history_plot(test_id, field, last_n=None):
    field = field.lower()
    if field not in FIELDS:
        return None
   
    date, value = __history__(test_id, field, last_n)
    xaxis = dates.datestr2num(date) 
    plt.figure()
    plt.plot_date(xaxis, value, ls='-', marker='.', xdate=True, tz=None)
    plt.xlabel("date")
    plt.ylabel(field)
    fname = f'plot_{test_id}_{field}'
    if last_n is not None:
        fname += f'_{last_n}.jpg'
    else:
        fname += '.jpg'
    path = os.path.join(PLT_PATH, fname)
    plt.gcf().autofmt_xdate()
    plt.savefig(path)
    return path