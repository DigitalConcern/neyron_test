import logging
from aiohttp import web
from application.photo import handlers, middleware

app = web.Application(middlewares=[middleware.auth_required_middleware])

app.router.add_post('/image', handlers.post_handler)
app.router.add_get('/image', handlers.get_handler)
app.router.add_get('/logs', handlers.logs_handler)
