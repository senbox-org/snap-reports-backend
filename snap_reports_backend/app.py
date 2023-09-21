import sys
import os
from sanic import Sanic
from sanic_cors import CORS

from api import api

def create_app() -> Sanic:
    app = Sanic(name='Reports')
    app.blueprint(api)
    CORS(app)

    # Production
    if os.getenv('MYSQL_DATABASE') != None:
        db_settings = {
            'DB_MODE': 'MYSQL',
            'DB': os.getenv('MYSQL_USER') + ':' + os.getenv('MYSQL_PASSWORD') + '@0.0.0.0:3306/' + os.getenv('MYSQL_DATABASE'),
            'PORT': 9090
        }
        app.config.update(db_settings)
        return app

    # Locally
    CFG_FILE = sys.argv[1]

    if os.path.exists(CFG_FILE+'.local'):
        CFG_FILE += '.local'

    app.config.update_config(CFG_FILE)

    return app