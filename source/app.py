import logging
from aiohttp import web
from application.photo import handlers, middleware

logging.basicConfig(level=logging.DEBUG, filename='myapp.log',
                    format='%(asctime)s,%(msecs)d: %(levelname)s: %(message)s')

app = web.Application(middlewares=[middleware.auth_required_middleware])

app.router.add_post('/image', handlers.post_handler)
app.router.add_get('/image', handlers.get_handler)
app.router.add_get('/logs', handlers.logs_handler)
