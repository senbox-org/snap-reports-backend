"""
Simple backend for SNAP REPORT utility.

author: Martino Ferrari (CS Group)
email: martino.ferrari@c-s.fr
"""
from sanic.response import text
from support import APP

from api import api


@APP.route("/favicon.ico")
async def favicon(_):
    """Solve faviocon warnings."""
    return text("NO ICON", status=404)


if __name__ == "__main__":
    APP.blueprint(api)
    APP.run(
        host="0.0.0.0",
        port=APP.config.PORT,
        workers=4,
        access_log=False,
        debug=False)
