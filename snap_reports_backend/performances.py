"""
Perforamnces and plots functions.

author: Martino Ferrari (CS Group)
email: martino.ferrari@c-s.fr
"""
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from sanic.response import text, json

from support import DB

CWD = os.path.abspath(os.getcwd())
PLT_PATH = os.path.join(CWD, 'plots')

if not os.path.isdir(PLT_PATH):
    os.mkdir(PLT_PATH)

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


def test_summary(test_id):
    """
    Test summary.
    """
    if test_id is None:
        return text("Test not found", status=404)
    rows = DB.execute(f"""
    SELECT
        result, duration, cpu_time, cpu_usage_avg, memory_avg, memory_max,
        io_write, io_read, threads_avg
    FROM results
    WHERE test={test_id}
    """)
    rows = rows.fetchall()
    if not rows:
        return text("No rows found", status=500)
    return __parse_results__(rows)


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


def test_reference(test_id):
    """
    Test summary.
    """
    if test_id is None:
        return text("Test not found", status=404)
    rows = DB.execute(f"""
            SELECT
                updated, duration, cpu_time, cpu_usage_avg, memory_avg,
                memory_max, io_write, io_read, threads_avg
            FROM reference_values
            WHERE test={test_id}
        """)
    row = rows.fetchone()
    if not row:
        return text("No reference found", status=404)
    return json(dict(row))


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


def history(test_id, tag, field, last_n=None):
    """
    Retrives the historic values of a specific field of a given test.
    """
    field = field.lower()
    if field not in FIELDS:
        return text("Field not valid", status=500)

    date, value = __history__(test_id, tag, field, last_n)
    return json({
        'date': date,
        'value': value
    })



def history_plot(test_id, tag, field, last_n=None):
    """
    Plot historic values of a field of a given test.
    """
    field = field.lower()
    if field not in FIELDS:
        return None
    reference = __get_reference__(test_id, field)
    date, value = __history__(test_id, tag, field, last_n)
    xaxis = dates.datestr2num(date)
    plt.figure()
    plt.plot_date(xaxis, value, ls='-', marker='.', xdate=True, tz=None,
                  label='historic values')
    if reference:
        plt.axhline(reference, c='black', ls='--', alpha=0.5,
                    label='reference')
    plt.axhline(np.mean(value), ls='--', alpha=0.5, c='C2', label='average')
    plt.xlabel("date")
    plt.ylabel(field)
    plt.gcf().autofmt_xdate()
    plt.legend()
    plt.grid(alpha=0.5)
    fname = f'plot_{test_id}_{field}'
    if last_n is not None:
        fname += f'_{last_n}.jpg'
    else:
        fname += '.jpg'
    path = os.path.join(PLT_PATH, fname)
    plt.savefig(path)
    return path


def history_plot_moving_average(test_id, tag, field, window, last_n=None,
                                compare=False):
    """
    Plot moving average of historic values of a field of a given test.
    """
    field = field.lower()
    if field not in FIELDS:
        return None
    reference = __get_reference__(test_id, field)
    date, value = __history__(test_id, tag, field, last_n)
    avg = np.mean(value)
    xaxis = dates.datestr2num(date)
    sub_x = []
    sub_y = []
    for i in range(window, len(xaxis)):
        sub_x.append(np.mean(xaxis[i-window:i]))
        sub_y.append(np.mean(value[i-window:i]))
    plt.figure()
    if compare:
        plt.plot_date(xaxis, value, ls='-', marker='.', color='C1', xdate=True,
                      tz=None, alpha=0.8, label='raw values')
    plt.plot_date(sub_x, sub_y, ls='-', marker='.', color='C0', xdate=True,
                  tz=None, label='moving average')
    if reference:
        plt.axhline(reference, c='black', ls='--', alpha=0.5,
                    label='reference')
    plt.axhline(avg, ls='--', alpha=0.5, c='C2', label='average')
    plt.xlabel("date")
    plt.ylabel(field)
    plt.gcf().autofmt_xdate()
    plt.legend()
    plt.grid(alpha=0.5)
    fname = f'plot_{test_id}_{field}'
    if last_n is not None:
        fname += f'_{last_n}.jpg'
    else:
        fname += '.jpg'
    path = os.path.join(PLT_PATH, fname)
    plt.savefig(path)
    return path
