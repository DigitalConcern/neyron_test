import asyncio
from aiohttp import web
from source import app
from application import database


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(database.make_migrations())
    web.run_app(app.app, host="127.0.0.1", port=8080)
