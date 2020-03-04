"""Implement api/reference apis."""
from sanic import Blueprint
from sanic.response import json

from support import DB
import support

reference = Blueprint('api_reference', url_prefix='/reference')


@reference.route("/list")
async def get_references(_):
    """Retrieve list of references."""
    rows = DB.execute("""
    SELECT
        id, test, referenceTag, updated, duration, cpu_time, cpu_usage_avg,
        cpu_usage_max, memory_avg, memory_max, io_write, io_read, threads_avg,
        threads_max
    FROM reference_values;""")
    res = []
    for row in rows:
        val = dict(row)
        val['test'] = support.get_test(val['test'])
        res.append(val)
    return json({'references': res})