import dataclasses
import json
import logging
from contextlib import asynccontextmanager
from functools import partial

import asyncclick as click
import trio
from pydantic import ValidationError
from trio_websocket import serve_websocket, ConnectionClosed

from models import Bus, WindowBounds
from serializers import WindowBoundsSerializer, BusSerializer
from utils.decorators import suppress
from utils.setup import setup_logger


DELAY = 0.5
buses = {}
logger = logging.getLogger('server')


@asynccontextmanager
async def handle_errors(ws):
    try:
        yield

    except ValidationError as error:
        await ws.send_message(error.json())


@suppress(ConnectionClosed)
async def fetch_coordinates(request):
    ws = await request.accept()
    global buses

    while True:
        async with handle_errors(ws):
            message = await ws.get_message()
            bus = BusSerializer.parse_raw(message).dict()
            buses[bus['busId']] = Bus(**bus)


async def send_buses(ws, bounds):
    buses_inside = [dataclasses.asdict(bus) for bus in buses.values() if bus.is_inside(bounds)]
    logger.debug(f'{len(buses_inside)} buses inside bounds')

    if not buses_inside:
        return

    message = {
        "msgType": "Buses",
        "buses": buses_inside
    }

    await ws.send_message(json.dumps(message, ensure_ascii=False))


@suppress(ConnectionClosed)
async def talk_to_browser(ws, bounds):
    while True:
        await send_buses(ws, bounds)
        await trio.sleep(DELAY)


@suppress(ConnectionClosed)
async def listen_browser(ws, bounds):
    while True:
        async with handle_errors(ws):
            message = await ws.get_message()
            bounds_data = WindowBoundsSerializer.parse_raw(message).dict()

            bounds.update(**bounds_data['data'])
            logger.debug(message)


async def handle_browser(request, bounds):
    ws = await request.accept()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(talk_to_browser, ws, bounds)
        nursery.start_soon(listen_browser, ws, bounds)


@click.command()
@click.option(
    '--host',
    default='127.0.0.1',
    help='Адрес хоста',
)
@click.option(
    '--bus-port',
    default=8080,
    help='Порт для имитатора автобусов',
)
@click.option(
    '--browser-port',
    default=8000,
    help='Порт для браузера',
)
@click.option(
    '-v',
    is_flag=True,
    help='Настройка логирования',
)
@suppress(KeyboardInterrupt)
async def main(host, bus_port, browser_port, v):
    if v:
        setup_logger(logger, level=logging.DEBUG)

    bounds = WindowBounds()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(
            partial(serve_websocket, fetch_coordinates, host, bus_port, ssl_context=None)
        )
        nursery.start_soon(
            partial(serve_websocket, partial(handle_browser, bounds=bounds), host, browser_port, ssl_context=None)
        )


if __name__ == '__main__':
    main(_anyio_backend="trio")
