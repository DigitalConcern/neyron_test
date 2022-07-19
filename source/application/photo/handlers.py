from io import BytesIO
from PIL import Image
import uuid
import asyncpg

import aiohttp
from aiohttp import web

from application import database


async def get_handler(request: aiohttp.request):
    image_id = request.rel_url.query["id"]

    connection = await database.connect()
    try:
        image_bin = await connection.fetchval("SELECT image_bin FROM photos_test WHERE id = $1", image_id)
    except asyncpg.exceptions.DataError:
        return web.Response(status=404)
    await connection.close()

    return web.Response(text=str(image_bin), status=200)


async def post_handler(request: aiohttp.request):
    image_bin = await request.read()

    with BytesIO() as bytes_stream:
        imageObj = Image.open(BytesIO(image_bin))

        if imageObj.format != "JPEG":
            imageObj = imageObj.convert("RGB")

        try:
            x = int(request.rel_url.query["x"])
        except KeyError:
            x = None

        try:
            y = int(request.rel_url.query["y"])
        except KeyError:
            y = None

        if x and y:
            imageObj.thumbnail((x, y))
        elif x:
            x_percent = (x / float(imageObj.size[0]))
            y = int((float(imageObj.size[0]) * float(x_percent)))
            imageObj.thumbnail((x, y))
        elif y:
            y_percent = (y / float(imageObj.size[1]))
            x = int((float(imageObj.size[1]) * float(y_percent)))
            imageObj.thumbnail((x, y))

        try:
            quality = request.rel_url.query["quality"]
            imageObj.save(bytes_stream, format='JPEG', quality=int(quality))
        except KeyError:
            imageObj.save(bytes_stream, format='JPEG')

        bytes_arr = bytes_stream.getvalue()

    unique_id = uuid.uuid4()

    connection = await database.connect()
    await connection.execute("INSERT INTO photos_test (id, image_bin) VALUES ($1, $2)", unique_id, bytes_arr)
    await connection.close()

    return web.Response(text=str(unique_id), status=200)


async def logs_handler(request: aiohttp.request):
    logs = open("myapp.log")
    return web.Response(text="".join(logs.readlines()), status=200)
