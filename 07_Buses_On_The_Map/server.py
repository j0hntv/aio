import dataclasses
import json
import logging
from functools import partial

import trio
from trio_websocket import serve_websocket, ConnectionClosed

from models import Bus, WindowBounds
from utils.decorators import suppress


DELAY = 1
FETCH_SOCKET = ('127.0.0.1', 8080)
SEND_SOCKET = ('127.0.0.1', 8000)
buses = {}
bounds = WindowBounds()
logger = logging.getLogger('server')


async def fetch_coordinates(request):
    ws = await request.accept()
    global buses

    while True:
        try:
            message = json.loads(await ws.get_message())
            buses[message['busId']] = Bus(**message)
        except ConnectionClosed:
            break


async def send_buses(ws):
    buses_inside = [dataclasses.asdict(bus) for bus in buses.values() if bus.is_inside(bounds)]
    logger.debug(f'{len(buses_inside)} buses inside bounds')
    message = {
        "msgType": "Buses",
        "buses": buses_inside
    }
    await ws.send_message(json.dumps(message, ensure_ascii=False))


@suppress(ConnectionClosed)
async def talk_to_browser(ws):
    while True:
        await send_buses(ws)
        await trio.sleep(DELAY)


@suppress(ConnectionClosed)
async def listen_browser(ws):
    while True:
        global bounds
        message = json.loads(await ws.get_message())
        bounds.update(**message['data'])
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
