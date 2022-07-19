from io import BytesIO
from PIL import Image

import uuid
import asyncpg

import aiohttp
from aiohttp import web

from application import database

import logging

from application.log_adapter import CustomAdapter

logging.basicConfig(level=logging.DEBUG, filename='myapp.log',
                    format="%(asctime)s: %(funcName)s: %(levelname)s: %(message)s")

logger = logging.getLogger(__name__)
logger = CustomAdapter(logger, {"route": None})


async def get_handler(request: aiohttp.request):
    image_id = request.rel_url.query["id"]

    logger.info('запрос на получение изображения', route=str(request.method) + " " + str(request.rel_url))
    connection = await database.connect()
    try:
        image_bin = await connection.fetchval("SELECT image_bin FROM photos_test WHERE id = $1", image_id)
    except asyncpg.exceptions.DataError:
        return web.Response(status=404)
    await connection.close()
    logger.info('изображение получено', route=str(request.method) + " " + str(request.rel_url))

    return web.Response(text=str(image_bin), status=200)


async def post_handler(request: aiohttp.request):
    image_bin = await request.read()

    logger.info('запрос на загрузку изображения', route=str(request.method) + " " + str(request.rel_url))
    with BytesIO() as bytes_stream:
        imageObj = Image.open(BytesIO(image_bin))

        if imageObj.format != "JPEG":
            logger.info(f'получено изображение в формате {imageObj.format}',
                        route=str(request.method) + " " + str(request.rel_url))
            imageObj = imageObj.convert("RGB")

        try:
            x = int(request.rel_url.query["x"])
            logger.debug(f'необязательный параметр x',
                         route=str(request.method) + " " + str(request.rel_url))
        except KeyError:
            x = None

        try:
            y = int(request.rel_url.query["y"])
            logger.debug(f'необязательный параметр y',
                         route=str(request.method) + " " + str(request.rel_url))
        except KeyError:
            y = None

        if x and y:
            imageObj.thumbnail((x, y))
            logger.info(f'размер изображения изменен по двум параметрам',
                        route=str(request.method) + " " + str(request.rel_url))
        elif x:
            x_percent = (x / float(imageObj.size[0]))
            y = int((float(imageObj.size[0]) * float(x_percent)))
            imageObj.thumbnail((x, y))
            logger.info(f'размер изображения изменен по параметру x',
                        route=str(request.method) + " " + str(request.rel_url))
        elif y:
            y_percent = (y / float(imageObj.size[1]))
            x = int((float(imageObj.size[1]) * float(y_percent)))
            imageObj.thumbnail((x, y))
            logger.info(f'размер изображения изменен по параметру y',
                        route=str(request.method) + " " + str(request.rel_url))

        try:
            quality = request.rel_url.query["quality"]
            imageObj.save(bytes_stream, format='JPEG', quality=int(quality))
            logger.debug(f'качество изображения изменено',
                         route=str(request.method) + " " + str(request.rel_url))
        except KeyError:
            imageObj.save(bytes_stream, format='JPEG')

        bytes_arr = bytes_stream.getvalue()

    unique_id = uuid.uuid4()

    connection = await database.connect()
    await connection.execute("INSERT INTO photos_test (id, image_bin) VALUES ($1, $2)", unique_id, bytes_arr)
    await connection.close()

    logger.info(f'изображение успешно сохранено',
                route=str(request.method) + " " + str(request.rel_url))
    return web.Response(text=str(unique_id), status=200)


async def logs_handler(request: aiohttp.request):
    logs = open("myapp.log")
    logger.info(f'выгружены логи',
                route=str(request.method) + " " + str(request.rel_url))
    return web.Response(text="".join(logs.readlines()), status=200)
