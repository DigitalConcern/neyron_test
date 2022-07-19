from aiohttp import web

import logging

from application.log_adapter import CustomAdapter

logging.basicConfig(level=logging.DEBUG, filename='myapp.log',
                    format="%(asctime)s: %(funcName)s: %(levelname)s: %(message)s")

logger = logging.getLogger(__name__)
logger = CustomAdapter(logger, {"route": None})


@web.middleware
async def auth_required_middleware(request, handler):
    if request.headers.get('Authorization') == 'Bearer 12345':
        logger.info('авторизованный запрос', route=str(request.method) + " " + str(request.rel_url))
        return await handler(request)
    logger.info('запрос без авторизации', route=str(request.method) + " " + str(request.rel_url))
    return web.Response(status=401)
