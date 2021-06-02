import os
import aiohttp
from aiohttp import web
from faker import Faker

WS_FILE = os.path.join(os.path.dirname(__file__), "index.html")


def get_random_name():
    fake = Faker()
    return fake.name()


async def index(request):
    ws_current = web.WebSocketResponse()
    ws_ready = ws_current.can_prepare(request)
    if not ws_ready.ok:
        with open(WS_FILE, "rb") as fp:
            return web.Response(body=fp.read(), content_type="text/html")

    await ws_current.prepare(request)

    name = get_random_name()

    await ws_current.send_json({'action': 'connect', 'name': name})

    for ws in request.app['websockets'].values():
        await ws.send_json({'action': 'join', 'name': name})
    request.app['websockets'][name] = ws_current

    count = 0
    while True:
        msg = await ws_current.receive()
        if msg.type == aiohttp.WSMsgType.text:
            count += 1
            for ws in request.app['websockets'].values():
                await ws.send_json(
                    {'action': 'sent', 'name': name, 'text': str(count) + '. ' + msg.data})
        else:
            break

    del request.app['websockets'][name]
    for ws in request.app['websockets'].values():
        await ws.send_json({'action': 'disconnect', 'name': name})

    return ws_current


async def init_app():

    app = web.Application()

    app['websockets'] = {}
    app.on_shutdown.append(shutdown)
    app.router.add_get('/', index)

    return app


async def shutdown(app):
    for ws in app['websockets'].values():
        await ws.close()
    app['websockets'].clear()


def main():
    app = init_app()
    web.run_app(app)


if __name__ == '__main__':
    main()
