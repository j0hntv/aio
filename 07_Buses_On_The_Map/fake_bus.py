import json
import logging
import random
import sys

import asyncclick as click
import trio
from trio_websocket import open_websocket_url

from utils.decorators import suppress, relaunch_on_disconnect
from utils.routes import load_routes
from utils.setup import setup_logger


RELAUNCH_DELAY = 3
logger = logging.getLogger('fake_bus')


def generate_bus_id(emulator_id, route_id, bus_index):
    bus_id = f'{route_id}-{bus_index}'
    if emulator_id:
        bus_id = f'{emulator_id}-{bus_id}'
    return bus_id


async def run_bus(send_channel, bus_id, route, start_offset, refresh_timeout):
    async with send_channel:
        route = route[start_offset:] + route[:start_offset]
        while True:
            for coordinates in route:
                lat, lng = coordinates
                message = {'busId': bus_id, 'lat': lat, 'lng': lng, 'route': bus_id}
                await send_channel.send(json.dumps(message, ensure_ascii=False))
                await trio.sleep(refresh_timeout)


@relaunch_on_disconnect(logger=logger, delay=RELAUNCH_DELAY)
async def send_updates(server_address, receive_channel):
    async with open_websocket_url(server_address, ssl_context=None) as ws:
        async with receive_channel:
            async for message in receive_channel:
                await ws.send_message(message)


@click.command()
@click.option(
    '--server',
    default='ws://127.0.0.1:8080',
    help='Адрес сервера',
)
@click.option(
    '--routes-number',
    default=-1,
    help='Количество маршрутов',
)
@click.option(
    '--buses-per-route',
    default=1,
    help='Количество автобусов на каждом маршруте',
)
@click.option(
    '--websockets-number',
    default=5,
    help='Количество открытых веб-сокетов',
)
@click.option(
    '--emulator-id',
    default='',
    help='Префикс к busId на случай запуска нескольких экземпляров имитатора',
)
@click.option(
    '--refresh-timeout',
    default=1,
    help='Задержка в обновлении координат сервера',
)
@click.option(
    '--buffer-size',
    default=0,
    help='Максимальное количество элементов, которое может быть буферизовано в канале перед блокировкой',
)
@click.option(
    '--directory-path',
    default='routes',
    help='Путь к файлам с маршрутами',
)
@click.option(
    '-v',
    is_flag=True,
    help='Настройка логирования',
)
@suppress(KeyboardInterrupt)
async def main(
    server, routes_number, buses_per_route, websockets_number,
    emulator_id, refresh_timeout, buffer_size, directory_path, v
):

    if v:
        setup_logger(logger, level=logging.DEBUG)

    try:
        async with trio.open_nursery() as nursery:
            channels = [trio.open_memory_channel(buffer_size) for _ in range(websockets_number)]
            for channel in channels:
                receive_channel = channel[1]
                nursery.start_soon(send_updates, server, receive_channel)

            for route in load_routes(directory_path, routes_number):
                for bus_index in range(buses_per_route):
                    send_channel = random.choice(channels)[0]
                    bus_id = generate_bus_id(emulator_id, route['name'], bus_index)
                    start_offset = random.randrange(len(route['coordinates']))
                    nursery.start_soon(
                        run_bus,
                        send_channel,
                        bus_id,
                        route['coordinates'],
                        start_offset,
                        refresh_timeout
                    )

    except OSError as ose:
        logger.error(f'Connection attempt failed: {ose}')


if __name__ == '__main__':
    main(_anyio_backend="trio")
