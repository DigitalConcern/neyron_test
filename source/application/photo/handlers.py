import datetime
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
    image_id = request.rel_url.query["id"]

    logger.info('запрос на получение изображения', route=str(request.method) + " " + str(request.rel_url))
    connection = await database.connect()
    try:
        image_bin = await connection.fetchval("SELECT image_bin FROM photos_test WHERE id = $1", image_id)
    except asyncpg.exceptions.DataError:
        return web.Response(status=404)
    await connection.close()
    logger.info('изображение получено', route=str(request.method) + " " + str(request.rel_url))

    im = Image.open(BytesIO(image_bin))
    im.show()

    return web.Response(text=str(image_bin), status=200)


async def image_post_handler(request: web.Request):
    image_bin = await request.read()

    logger.info('запрос на загрузку изображения', route=str(request.method) + " " + str(request.rel_url))
    with BytesIO() as bytes_stream:
        try:
            imageObj = Image.open(BytesIO(image_bin))
        except:
            return web.Response(status=400)

        if imageObj.format != "JPEG":
            logger.info(f'получено изображение в формате {imageObj.format}',
                        route=str(request.method) + " " + str(request.rel_url))
            imageObj = imageObj.convert("RGB")

        try:
            x = request.rel_url.query["x"]
            try:
                x = int(x)
            except ValueError:
                return web.Response(status=400)
            logger.debug(f'необязательный параметр x',
                         route=str(request.method) + " " + str(request.rel_url))
        except KeyError:
            x = None

        try:
            y = request.rel_url.query["y"]
            try:
                y = int(y)
            except ValueError:
                return web.Response(status=400)
            logger.debug(f'необязательный параметр y',
                         route=str(request.method) + " " + str(request.rel_url))
        except KeyError:
            y = None

        if x and y:
            imageObj.thumbnail((x, y))
            logger.info(f'размер изображения изменен по двум параметрам',
                        route=str(request.method) + " " + str(request.rel_url))
        # В случае, если задан только один параметр размера, второй высчитывается через начальное соотношение сторон
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
            try:
                quality = int(quality)
            except ValueError:
                return web.Response(status=400)
            imageObj.save(bytes_stream, format='JPEG', quality=quality)
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


async def registration_handler(request: web.Request):
    data = await request.json()

    try:
        unique_user_id = uuid.uuid5(uuid.NAMESPACE_DNS, str(data['email']) + str(data['password']))
    except KeyError:
        return web.Response(status=400)

    logger.info('запрос на регистрацию', route=str(request.method) + " " + str(request.rel_url))

    access_token = uuid.uuid4()

    connection = await database.connect()
    try:
        await connection.execute("INSERT INTO auth_users (id, email, password, access_token, time_create) VALUES ($1, "
                                 "$2, $3, $4, $5)",
                                 unique_user_id,
                                 str(data['email']),
                                 str(data['password']),
                                 access_token,
                                 datetime.datetime.now())
    except asyncpg.exceptions.UniqueViolationError:
        await connection.execute("UPDATE auth_users SET access_token=$1, time_create=$2 WHERE email=$3 AND password=$4",
                                 access_token,
                                 datetime.datetime.now(),
                                 str(data['email']),
                                 str(data['password']))
        return web.Response(text=str(access_token), status=409)
    await connection.close()

    logger.info('пользователь зарегистрирован', route=str(request.method) + " " + str(request.rel_url))

    return web.Response(text=str(access_token), status=200)


async def login_handler(request: web.Request):
    data = await request.json()

    logger.info('запрос на вход', route=str(request.method) + " " + str(request.rel_url))

    access_token = uuid.uuid4()

    connection = await database.connect()
    res = await connection.execute(
        "UPDATE auth_users SET access_token=$1, time_create=$2 WHERE email=$3 AND password=$4",
        access_token,
        datetime.datetime.now(),
        str(data['email']),
        str(data['password'])
    )
    if res == 'UPDATE 0':
        return web.Response(status=404)

    access_token = await connection.fetchval("SELECT access_token FROM auth_users WHERE email=$1 AND password=$2",
                                             str(data['email']),
                                             str(data['password']))

    await connection.close()

    logger.info('пользователь авторизован', route=str(request.method) + " " + str(request.rel_url))

    return web.Response(text=str(access_token), status=200)


async def logs_handler(request: web.Request):
    logs = open("myapp.log")
    logger.info(f'выгружены логи',
                route=str(request.method) + " " + str(request.rel_url))
    return web.Response(text="".join(logs.readlines()), status=200)
