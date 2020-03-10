"""Implement api/testset apis."""
from sanic import Blueprint
from sanic.response import json

from support import DB

testset = Blueprint('api_testset', url_prefix='/testset')


@testset.route("/list")
async def testset_list(_):
    """Retrieve list of testset."""
    rows = DB.fetchall("SELECT DISTINCT testset FROM tests")
    res = []
    for row in rows:
        res.append(row['testset'])
    return json({"testset": res})


@testset.route("/<name:string>")
async def testset_test_list(_, name):
    """Retrieve list of tests of a given testset."""
    rows = DB.fetchall(
        f"SELECT * FROM tests WHERE testset='{name}' ORDER BY id")
    return json({"tests": rows})
