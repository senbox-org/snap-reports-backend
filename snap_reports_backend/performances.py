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


def test_reference(test_id):
    """Get test references values."""
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


def __history_plt_ready__(test_id, tag, field, last_n):
    date, value = __history__(test_id, tag, field, last_n)
    xaxis = dates.datestr2num(date)
    return xaxis, value


def __history_mean_value__(test_id, tag, field, last_n):
    _, value = __history__(test_id, tag, field, last_n)
    return np.mean(value)


def __history_moving_avg__(test_id, tag, field, last_n, window):
    date, value = __history_plt_ready__(test_id, tag, field, last_n)
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


def history_plot(test_id, tag, field, last_n=None):
    """Plot historic values of a field of a given test."""
    field = field.lower()
    if field not in FIELDS:
        return None
    test = __get_test_name__(test_id)
    reference = __get_reference__(test_id, field)
    date, value = __history_plt_ready__(test_id, tag, field, last_n)
    plt.figure()
    plt.plot_date(date, value, ls='-', marker='.', xdate=True, tz=None,
                  label='historic values')
    if reference:
        plt.axhline(reference, c='C2', ls='--', alpha=0.5,
                    label='reference')
    plt.axhline(np.mean(value), ls='--', alpha=0.5, c='C0', label='average')
    plt.xlabel("date")
    plt.ylabel(field)
    plt.gcf().autofmt_xdate()
    plt.legend()
    plt.title(f'{test} - {tag}:{field}\nHistoric values')
    plt.grid(alpha=0.5)
    fname = f'plot_{tag}_{test_id}_{field}'
    if last_n is not None:
        fname += f'_{last_n}.jpg'
    else:
        fname += '.jpg'
    path = os.path.join(PLT_PATH, fname)
    plt.savefig(path)
    return path


def history_plot_moving_average(test_id, tag, field, window, last_n=None,
                                compare=False):
    """Plot moving average of historic values of a field of a given test."""
    field = field.lower()
    if field not in FIELDS:
        return None
    reference = __get_reference__(test_id, field)
    test = __get_test_name__(test_id)
    date, value = __history_moving_avg__(test_id, tag, field, last_n, window)
    plt.figure()
    avg = __history_mean_value__(test_id, tag, field, last_n)
    if compare:
        xs, ys = __history_plt_ready__(test_id, tag, field, last_n)
        plt.plot_date(xs, ys, ls='-', marker='.', color='C1', xdate=True,
                      tz=None, alpha=0.8, label='raw values')
    plt.plot_date(date, value, ls='-', marker='.', color='C0', xdate=True,
                  tz=None, label='moving average')
    if reference:
        plt.axhline(reference, c='C2', ls='--', alpha=0.5,
                    label='reference')
    plt.axhline(avg, ls='--', alpha=0.5, c='C0', label='average')
    plt.xlabel("date")
    plt.ylabel(field)
    plt.gcf().autofmt_xdate()
    plt.grid(alpha=0.5)
    plt.title(f'{test} - {tag}:{field}\nMoving average ({window}) ')
    plt.legend()
    fname = f'moving_average_{tag}_{window}_{test_id}_{field}'
    if last_n is not None:
        fname += f'_{last_n}.jpg'
    else:
        fname += '.jpg'
    path = os.path.join(PLT_PATH, fname)
    plt.savefig(path)
    return path


def relative_plot(test_id, tag, reference_tag, field, last_n=None, window=0):
    """Plot historic relatives values of a field of a given test."""
    field = field.lower()
    if field not in FIELDS:
        return None
    test = __get_test_name__(test_id)
    if window > 1:
        date, value = __history_moving_avg__(test_id, tag, field, last_n,
                                             window)
    else:
        date, value = __history_plt_ready__(test_id, tag, field, last_n)

    if reference_tag == 'mean':
        reference = np.mean(value)
    else:
        if reference_tag == 'reference':
            reference_tag = 'ref7'
        _, reference = __history__(test_id, reference_tag, field, last_n)
        reference = np.mean(reference)

    value = (value-reference)/reference * 100
    average = np.mean(value)

    plt.figure()
    plt.plot_date(date, value, ls='-', marker='.', color='C0',
                  tz=None, label='relative value (%)')
    plt.axhline(average, ls='--', c='C0', label='average')
    plt.xlabel("date")
    plt.ylabel(f'{field} (%)')
    plt.title(f'{test} - {field}\n{tag} relative to {reference_tag}')
    plt.gcf().autofmt_xdate()
    plt.grid(alpha=0.5)
    plt.legend()
    fname = f'relateive_{tag}_{reference_tag}_{test_id}_{field}'
    if last_n is not None:
        fname += f'_{last_n}.jpg'
    else:
        fname += '.jpg'
    path = os.path.join(PLT_PATH, fname)
    plt.savefig(path)
    return path


def get_status_dict(test_id, tag):
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
        'last': (1 - cpu_time[0] / ref_cpu_time) * 100,
        'last10': (1 - np.mean(cpu_time[:10]) / ref_cpu_time) * 100,
        'average': (1 - np.mean(cpu_time) / ref_cpu_time) * 100,
    }
    res['memory'] = {
        'last': (1 - memory[0] / ref_memory) * 100,
        'last10': (1 - np.mean(memory[:10]) / ref_memory) * 100,
        'average': (1 - np.mean(memory) / ref_memory) * 100,
    }
    res['read'] = {
        'last': (1 - read[0] / ref_read) * 100,
        'last10': (1 - np.mean(read[:10]) / ref_read) * 100,
        'average': (1 - np.mean(read) / ref_read) * 100,
    }
    return res


def get_status(test_id, tag):
    """Get branch test status."""
    res = get_status_dict(test_id, tag)
    if res is None:
        return text("No reference values found", status=500)
    return json(res)
