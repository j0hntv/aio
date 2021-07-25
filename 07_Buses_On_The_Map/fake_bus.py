import json
import random
import sys

import trio
from trio_websocket import open_websocket_url, ConnectionClosed

from utils.decorators import suppress
from utils.routes import load_routes


URL = 'ws://127.0.0.1:8080'
DELAY = 1
MIN_ROUTE_BUSES = 1
MAX_ROUTE_BUSES = 5
MAX_CHANNELS = 5
MAX_BUFFER_SIZE = 0


def generate_bus_id(route_id, bus_index):
    return f'{route_id}-{bus_index}'


async def run_bus(send_channel, bus_id, route, start_offset):
    async with send_channel:
        route = route[start_offset:] + route[:start_offset]
        while True:
            for coordinates in route:
                lat, lng = coordinates
                message = {'busId': bus_id, 'lat': lat, 'lng': lng, 'route': bus_id}
                await send_channel.send(json.dumps(message, ensure_ascii=False))
                await trio.sleep(DELAY)


async def send_updates(server_address, receive_channel):
    async with open_websocket_url(server_address) as ws:
        async with receive_channel:
            async for message in receive_channel:
                await ws.send_message(message)


@suppress(KeyboardInterrupt, ConnectionClosed)
async def main():
    try:
        async with trio.open_nursery() as nursery:
            channels = [trio.open_memory_channel(MAX_BUFFER_SIZE) for _ in range(MAX_CHANNELS)]
            for bus_index in range(MIN_ROUTE_BUSES, MAX_ROUTE_BUSES):
                for route in load_routes():
                    send_channel = random.choice(channels)[0]
                    bus_id = generate_bus_id(route['name'], bus_index)
                    start_offset = random.randrange(len(route['coordinates']))
                    nursery.start_soon(run_bus, send_channel, bus_id, route['coordinates'], start_offset)

                receive_channel = random.choice(channels)[1]
                nursery.start_soon(send_updates, URL, receive_channel)

    except OSError as ose:
        print(f'Connection attempt failed: {ose}', file=sys.stderr)


if __name__ == '__main__':
    trio.run(main)
