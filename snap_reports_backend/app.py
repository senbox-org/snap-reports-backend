import sys
import os
from sanic import Sanic
from sanic_cors import CORS

from api import api

def create_app() -> Sanic:
    app = Sanic(name='Reports')
    app.blueprint(api)
    CORS(app)
    CFG_FILE = sys.argv[1]

    if os.path.exists(CFG_FILE+'.local'):
        CFG_FILE += '.local'

    app.config.update_config(CFG_FILE)

    return app