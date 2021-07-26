import json
import logging
from functools import partial

import trio
from trio_websocket import serve_websocket, ConnectionClosed

from utils.decorators import suppress


DELAY = 1
FETCH_SOCKET = ('127.0.0.1', 8080)
SEND_SOCKET = ('127.0.0.1', 8000)
buses = {}
logger = logging.getLogger('server')


async def fetch_coordinates(request):
    ws = await request.accept()
    global buses

    while True:
        try:
            message = json.loads(await ws.get_message())
            buses[message['busId']] = message
        except ConnectionClosed:
            break


@suppress(ConnectionClosed)
async def talk_to_browser(ws):
    while True:
        message = {
            "msgType": "Buses",
            "buses": list(buses.values())
        }
        await ws.send_message(json.dumps(message, ensure_ascii=False))
        await trio.sleep(DELAY)


@suppress(ConnectionClosed)
async def listen_browser(ws):
    while True:
        message = await ws.get_message()
        logger.debug(message)


async def handle_browser(request):
    ws = await request.accept()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(talk_to_browser, ws)
        nursery.start_soon(listen_browser, ws)


def setup_logger(logger, level):
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    logger.setLevel(level)


@suppress(KeyboardInterrupt)
async def main():
    setup_logger(logger, level=logging.DEBUG)
    async with trio.open_nursery() as nursery:
        nursery.start_soon(partial(serve_websocket, fetch_coordinates, *FETCH_SOCKET, ssl_context=None))
        nursery.start_soon(partial(serve_websocket, handle_browser, *SEND_SOCKET, ssl_context=None))


if __name__ == '__main__':
    trio.run(main)
