from aiohttp import web
from application.photo import handlers, middleware

app = web.Application(middlewares=[middleware.auth_required_middleware])

app.router.add_post('/image', handlers.image_post_handler)
app.router.add_post('/registration', handlers.registration_handler)
app.router.add_get('/login', handlers.login_handler)
app.router.add_get('/image', handlers.image_get_handler)
app.router.add_get('/logs', handlers.logs_handler)
