import asyncio
import ssl
from aiohttp import web, ClientSession
import uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

routes = {}

async def proxy_handler(request):
    path = '/' + request.path.split('/')[1] + '/'
    backend = routes.get(path)
    if not backend:
        return web.Response(text=f"No route for {path}", status=404)

    backend_url = backend + request.rel_url.path_qs

    async with ClientSession() as session:
        req = await session.request(
            method=request.method,
            url=backend_url,
            headers={key: value for key, value in request.headers.items() if key != 'Host'},
            data=await request.read()
        )
        body = await req.read()
        return web.Response(body=body, status=req.status, headers=req.headers)

async def add_route(request):
    data = await request.json()
    path = data.get('path')
    backend = data.get('backend')
    if path and backend:
        routes[path] = backend
        return web.Response(text=f"Added {path} -> {backend}")
    return web.Response(text="Invalid", status=400)

async def remove_route(request):
    data = await request.json()
    path = data.get('path')
    if path in routes:
        del routes[path]
        return web.Response(text=f"Removed {path}")
    return web.Response(text="Not found", status=404)

app = web.Application()
app.router.add_route('*', '/{tail:.*}', proxy_handler)
app.router.add_post('/admin/add_route', add_route)
app.router.add_post('/admin/remove_route', remove_route)

# === Configuración SSL ===
ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(certfile="/etc/letsencrypt/live/dws.com.co/fullchain.pem",
                            keyfile="/etc/letsencrypt/live/dws.com.co/privkey.pem")

web.run_app(app, port=443, ssl_context=ssl_context)


