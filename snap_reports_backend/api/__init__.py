"""Implementation of api server side."""
from sanic import Blueprint

from .test import test
from .branch import branch
from .job import job
from .reference import reference
from .testset import testset

api = Blueprint.group(test, branch, job, reference, testset, url_prefix='/api')
