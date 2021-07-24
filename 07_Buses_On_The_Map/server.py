from functools import partial
import json

import trio
from trio_websocket import serve_websocket, ConnectionClosed


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
            await trio.sleep(0.1)
        except ConnectionClosed:
            break


async def main():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(partial(serve_websocket, fetch_coordinates, '127.0.0.1', 8080, ssl_context=None))
        nursery.start_soon(partial(serve_websocket, talk_to_browser, '127.0.0.1', 8000, ssl_context=None))


if __name__ == '__main__':
    trio.run(main)
