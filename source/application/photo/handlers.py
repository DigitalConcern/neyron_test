import datetime
import json
from io import BytesIO
from PIL import Image

import uuid
import asyncpg

from aiohttp import web

from application import database

import logging

from application.log_adapter import CustomAdapter

logging.basicConfig(level=logging.DEBUG, filename='myapp.log',
                    format="%(asctime)s: %(funcName)s: %(levelname)s: %(message)s")

logger = logging.getLogger(__name__)
logger = CustomAdapter(logger, {"route": None})


async def image_get_handler(request: web.Request):
    try:
        image_id = request.rel_url.query["id"]
    except KeyError:
        logger.debug('bad request - неверный параметр запроса', route=str(request.method) + " " + str(request.rel_url))
        return web.Response(status=400)

    connection = await database.connect()
    try:
        image_bin = await connection.fetchval("SELECT image_bin FROM photos_test WHERE id = $1", image_id)
    except asyncpg.exceptions.DataError:
        logger.debug('изображение не найдено', route=str(request.method) + " " + str(request.rel_url))
        return web.Response(status=404)
    await connection.close()

    if image_bin is None:
        return web.Response(status=404)
    else:
        return web.Response(text=str(image_bin), status=200)


async def image_post_handler(request: web.Request):
    image_bin = await request.read()

    with BytesIO() as bytes_stream:
        try:
            imageObj = Image.open(BytesIO(image_bin))
        except:
            logger.debug('bad request - некорректный формат изображения',
                         route=str(request.method) + " " + str(request.rel_url))
            return web.Response(status=400)

        if imageObj.format != "JPEG":
            imageObj = imageObj.convert("RGB")

        try:
            x = request.rel_url.query["x"]
            try:
                x = int(x)
                if x <= 0:
                    logger.debug('bad request - неверный параметр запроса',
                                 route=str(request.method) + " " + str(request.rel_url))
                    return web.Response(status=400)
            except ValueError:
                logger.debug('bad request - неверный параметр запроса', route=str(request.method) + " " + str(request.rel_url))
                return web.Response(status=400)
        except KeyError:
            x = None

        try:
            y = request.rel_url.query["y"]
            try:
                y = int(y)
                if y <= 0:
                    logger.debug('bad request - неверный параметр запроса',
                                 route=str(request.method) + " " + str(request.rel_url))
                    return web.Response(status=400)
            except ValueError:
                logger.debug('bad request - неверный параметр запроса',
                             route=str(request.method) + " " + str(request.rel_url))
                return web.Response(status=400)
        except KeyError:
            y = None

        if x and y:
            imageObj.thumbnail((x, y))
        # В случае, если задан только один параметр размера, второй высчитывается через начальное соотношение сторон
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
            try:
                quality = int(quality)
            except ValueError:
                logger.debug('bad request - неверный параметр запроса',
                             route=str(request.method) + " " + str(request.rel_url))
                return web.Response(status=400)
            imageObj.save(bytes_stream, format='JPEG', quality=quality)
        except KeyError:
            imageObj.save(bytes_stream, format='JPEG')

        bytes_arr = bytes_stream.getvalue()

    unique_id = uuid.uuid4()

    connection = await database.connect()
    await connection.execute("INSERT INTO photos_test (id, image_bin) VALUES ($1, $2)", unique_id, bytes_arr)
    await connection.close()

    return web.Response(text=str(unique_id), status=200)


async def registration_handler(request: web.Request):
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        logger.debug('bad request - некорректное тело запроса', route=str(request.method) + " " + str(request.rel_url))
        return web.Response(status=400)

    try:
        email = data['email']
        password = data['password']
        try:
            email = str(email)
            password = str(password)
        except ValueError:
            logger.debug('bad request - неверный формат данных',
                         route=str(request.method) + " " + str(request.rel_url))
            return web.Response(status=400)
    except KeyError:
        logger.debug('bad request  - некорректный json', route=str(request.method) + " " + str(request.rel_url))
        return web.Response(status=400)

    unique_user_id = uuid.uuid5(uuid.NAMESPACE_DNS, email + password)

    access_token = uuid.uuid4()

    connection = await database.connect()
    try:
        await connection.execute("INSERT INTO users (id, email, password) VALUES ($1, $2, $3)",
                                 unique_user_id,
                                 email,
                                 password)
        await connection.execute("INSERT INTO auth (user_id, access_token, time_create) VALUES ($1, $2, $3)",
                                 unique_user_id,
                                 access_token,
                                 datetime.datetime.now())
    except asyncpg.exceptions.UniqueViolationError:
        logger.debug('такой пользователь уже есть', route=str(request.method) + " " + str(request.rel_url))
        return web.Response(text=str(access_token), status=409)
    await connection.close()

    logger.info('пользователь зарегистрирован', route=str(request.method) + " " + str(request.rel_url))

    return web.Response(text=str(access_token), status=200)


async def login_handler(request: web.Request):
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        logger.debug('bad request - некорректное тело запроса', route=str(request.method) + " " + str(request.rel_url))
        return web.Response(status=400)

    try:
        email = data['email']
        password = data['password']
        try:
            email = str(email)
            password = str(password)
        except ValueError:
            logger.debug('bad request - неверный формат данных',
                         route=str(request.method) + " " + str(request.rel_url))
            return web.Response(status=400)
    except KeyError:
        logger.debug('bad request  - некорректный json', route=str(request.method) + " " + str(request.rel_url))
        return web.Response(status=400)

    access_token = uuid.uuid4()

    connection = await database.connect()

    unique_user_id = await connection.fetchval(
        "SELECT id FROM users WHERE email=$1 and password=$2",
        email,
        password
    )
    if unique_user_id is None:
        logger.debug('пользователь не найден', route=str(request.method) + " " + str(request.rel_url))
        return web.Response(status=404)

    await connection.execute(
        "INSERT INTO auth (user_id, access_token, time_create) VALUES ($1, $2, $3)",
        unique_user_id,
        access_token,
        datetime.datetime.now()
    )

    await connection.close()

    return web.Response(text=str(access_token), status=200)


async def logs_handler(request: web.Request):
    logs = open("myapp.log")
    return web.Response(text="".join(logs.readlines()), status=200)
