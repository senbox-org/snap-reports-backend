"""
Simple script to refresh references.
"""
import sqlite3
import datetime as dt
import sys


SELECT_QUERY = """
SELECT
    test, duration, cpu_time, cpu_usage_avg, cpu_usage_max,
    memory_avg, memory_max, io_write, io_read, threads_avg, threads_max
FROM results
WHERE
    result =
        (SELECT ID FROM resultTags WHERE tag = "SUCCESS")
    AND job IN
        (SELECT ID FROM jobs WHERE dockerTag =
            (SELECT ID FROM dockerTags WHERE name = "snap:ref7"));
"""

CLEAR_REFRENCES = """
DELETE FROM reference_values;
"""

UPDATE_REFERENCES = """
INSERT INTO reference_values
    (test, referenceTag, updated, duration, cpu_time, cpu_usage_avg,
     cpu_usage_max, memory_avg, memory_max, io_write, io_read, threads_avg,
     threads_max, raw_data)
VALUES
    (:test, (SELECT ID FROM dockerTags WHERE name = "snap:ref7"), :updated,
     :duration, :cpu_time, :cpu_usage_avg, :cpu_usage_max, :memory_avg,
     :memory_max, :io_write, :io_read, :threads_avg, :threads_max, "");
"""

KEYS = ["duration", "cpu_time", "cpu_usage_avg", "cpu_usage_max", "memory_avg",
    "memory_max", "io_read", "io_write", "threads_avg", "threads_max"]

def __args__():
    args = sys.argv
    if len(args) != 2:
        print ('reportDB argument needed')
        sys.exit(1)
    return args[1]

def __sum_tests__(a, b):
    c = {
        'test': a['test'],
    }
    for key in KEYS:
        c[key] = a[key] + b[key]
    return c

def __update_reference__(db, tests):
    db.execute(CLEAR_REFRENCES)
    cursor = db.cursor()
    updated = str(dt.datetime.now())

    for i, test_id in enumerate(tests):
        print(f'\r{i+1:>3}/{len(tests)}', end='')
        test = tests[test_id]
        test['updated'] = updated
        cursor.execute(UPDATE_REFERENCES, test)
        db.commit()
    cursor.close()
    print()

if __name__ == "__main__":
    dbpath = __args__()
    db = sqlite3.connect(dbpath)
    db.row_factory = sqlite3.Row
    rows = db.execute(SELECT_QUERY)
    tests = {}
    tests_counter = {}
    for row in rows:
        test_id = row['test']
        if test_id not in tests:
            tests[test_id] = row
            tests_counter[test_id] = 1
        else:
            tests[test_id] = __sum_tests__(tests[test_id], row)
            tests_counter[test_id] += 1
    for test_id in tests:
        for key in KEYS:
            tests[test_id][key] /= tests_counter[test_id]
    __update_reference__(db, tests)
