import asyncio
from aiohttp import web
import app
from application import database


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(database.make_migrations())
    web.run_app(app.app, host="0.0.0.0", port=8080, access_log=None)
