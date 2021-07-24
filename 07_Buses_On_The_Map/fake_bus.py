import json
import random
import sys

import trio
from trio_websocket import open_websocket_url, ConnectionClosed

from utils.load_routes import load_routes


URL = 'ws://127.0.0.1:8080'
DELAY = 0.1
MIN_ROUTE_BUSES = 1
MAX_ROUTE_BUSES = 5


def generate_bus_id(route_id, bus_index):
    return f'{route_id}-{bus_index}'


async def run_bus(url, bus_id, route, start_offset):
    async with open_websocket_url(url) as ws:
        route = route[start_offset:] + route[:start_offset]
        while True:
            for coordinates in route:
                lat, lng = coordinates
                message = {'busId': bus_id, 'lat': lat, 'lng': lng, 'route': bus_id}
                await ws.send_message(json.dumps(message, ensure_ascii=False))
                await trio.sleep(DELAY)


async def main():
    try:
        async with trio.open_nursery() as nursery:
            for route in load_routes():
                for bus_index in range(MIN_ROUTE_BUSES, MAX_ROUTE_BUSES):
                    bus_id = generate_bus_id(route['name'], bus_index)
                    start_offset = random.randrange(len(route['coordinates']))
                    nursery.start_soon(run_bus, URL, bus_id, route['coordinates'], start_offset)

    except OSError as ose:
        print(f'Connection attempt failed: {ose}', file=sys.stderr)

    except (KeyboardInterrupt, ConnectionClosed):
        sys.exit()


if __name__ == '__main__':
    trio.run(main)
