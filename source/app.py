from aiohttp import web
from application.photo import handlers

app = web.Application()
app.router.add_post('/post', handlers.post_handler)
app.router.add_get('/get', handlers.get_handler)
