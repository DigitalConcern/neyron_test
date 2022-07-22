from uuid import UUID

from aiohttp import web
import datetime

import logging

from application.log_adapter import CustomAdapter
from application.database import connect

logging.basicConfig(level=logging.DEBUG, filename='myapp.log',
                    format="%(asctime)s: %(funcName)s: %(levelname)s: %(message)s")

logger = logging.getLogger(__name__)
logger = CustomAdapter(logger, {"route": None})


@web.middleware
async def auth_required_middleware(request, handler):
    if str(request.rel_url) != '/login' and str(request.rel_url) != '/registration':
        try:
            token = UUID(request.headers.get('Authorization')[7:])
        except:
            logger.debug('запрос без авторизации', route=str(request.method) + " " + str(request.rel_url))
            return web.Response(status=401)

        connection = await connect()

        time_create = await connection.fetchval(
            "SELECT time_create FROM auth WHERE access_token=$1",
            token
        )

        if time_create is None:
            logger.debug('запрос без авторизации', route=str(request.method) + " " + str(request.rel_url))
            await connection.close()
            return web.Response(status=401)

        if (datetime.datetime.now() - time_create).total_seconds() < 10*60:
            logger.debug('авторизованный запрос', route=str(request.method) + " " + str(request.rel_url))
            await connection.close()
            return await handler(request)
        else:
            logger.debug('запрос без авторизации', route=str(request.method) + " " + str(request.rel_url))
            await connection.close()
            return web.Response(status=401)
    else:
        return await handler(request)
