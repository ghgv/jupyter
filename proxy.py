import asyncio
import ssl
from aiohttp import web, ClientSession, WSMsgType
import uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

routes = {}

async def proxy_handler(request):
    path = '/' + request.path.split('/')[1] + '/'
    backend = routes.get(path)
    if not backend:
        return web.Response(text=f"No route for {path}", status=404)

    backend_url = backend + request.rel_url.path_qs
    print(f"[INFO] Proxying {request.method} {request.rel_url} -> {backend_url}")

    # === WebSocket support ===
    if request.headers.get('Upgrade', '').lower() == 'websocket':
        ws_server = web.WebSocketResponse()
        await ws_server.prepare(request)

        session = ClientSession()
        try:
            async with session.ws_connect(backend_url) as ws_client:
                async def forward(ws_from, ws_to):
                    async for msg in ws_from:
                        if msg.type == WSMsgType.TEXT:
                            await ws_to.send_str(msg.data)
                        elif msg.type == WSMsgType.BINARY:
                            await ws_to.send_bytes(msg.data)
                        elif msg.type == WSMsgType.CLOSE:
                            await ws_to.close()

                await asyncio.wait([
                    asyncio.create_task(forward(ws_server, ws_client)),
                    asyncio.create_task(forward(ws_client, ws_server)),
                ])
        except Exception as e:
            print(f"[ERROR] WebSocket proxy error: {e}")
            return web.Response(text="WebSocket proxy error", status=500)
        finally:
            await session.close()
        return ws_server

    # === HTTP proxy fallback ===
    async with ClientSession() as session:
        try:
            req = await session.request(
                method=request.method,
                url=backend_url,
                headers={key: value for key, value in request.headers.items() if key != 'Host'},
                data=await request.read(),
                allow_redirects=False
            )
            body = await req.read()
            return web.Response(body=body, status=req.status, headers=req.headers)
        except Exception as e:
            print(f"[ERROR] Proxy error: {e}")
            return web.Response(text="Proxy error", status=500)

async def add_route(request):
    data = await request.json()
    path = data.get('path')
    backend = data.get('backend')
    if path and backend:
        routes[path] = backend
        print(f"[INFO] Added {path} -> {backend}")
        return web.Response(text=f"Added {path} -> {backend}")
    return web.Response(text="Invalid payload", status=400)

async def remove_route(request):
    data = await request.json()
    path = data.get('path')
    if path in routes:
        del routes[path]
        print(f"[INFO] Removed {path}")
        return web.Response(text=f"Removed {path}")
    return web.Response(text="Path not found", status=404)

app = web.Application()
app.router.add_post('/admin/add_route', add_route)
app.router.add_post('/admin/remove_route', remove_route)
app.router.add_route('*', '/{tail:.*}', proxy_handler)

# === SSL Configuration ===
ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(
    certfile="/etc/letsencrypt/live/dws.com.co/fullchain.pem",
    keyfile="/etc/letsencrypt/live/dws.com.co/privkey.pem"
)

print("[INFO] Proxy SageMaker-like with WebSocket support running on :443")
web.run_app(app, port=443, ssl_context=ssl_context)
