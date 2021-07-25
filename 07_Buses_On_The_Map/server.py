import json
from functools import partial

import trio
from trio_websocket import serve_websocket, ConnectionClosed

from utils.decorators import suppress


DELAY = 1
FETCH_SOCKET = ('127.0.0.1', 8080)
SEND_SOCKET = ('127.0.0.1', 8000)
buses = {}


async def fetch_coordinates(request):
    ws = await request.accept()
    global buses

    while True:
        try:
            message = json.loads(await ws.get_message())
            buses[message['busId']] = message
        except ConnectionClosed:
            break


async def talk_to_browser(request):
    ws = await request.accept()

    while True:
        try:
            message = {
                "msgType": "Buses",
                "buses": list(buses.values())
            }
            await ws.send_message(json.dumps(message, ensure_ascii=False))
            await trio.sleep(DELAY)
        except ConnectionClosed:
            break


@suppress(KeyboardInterrupt)
async def main():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(partial(serve_websocket, fetch_coordinates, *FETCH_SOCKET, ssl_context=None))
        nursery.start_soon(partial(serve_websocket, talk_to_browser, *SEND_SOCKET, ssl_context=None))


if __name__ == '__main__':
    trio.run(main)
