import json
from io import BytesIO

import PIL
import asyncpg
from aiohttp import web


async def get_handler(request):
    data = await request.json()

    return web.Response(status=200)


async def post_handler(request):
    data = request.

    with open('pic1.jpg', 'wb') as handle:
        handle.write(result)

    return web.Response(status=200)
