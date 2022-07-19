from aiohttp import web


@web.middleware
async def auth_required_middleware(request, handler):
    if request.headers.get('Authorization') == 'Bearer 12345':
        return await handler(request)
    return web.Response(status=401)
