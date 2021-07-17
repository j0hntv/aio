import json
import sys

import trio
from trio_websocket import open_websocket_url

from utils.load_routes import load_routes


DELAY = 1
URL = 'ws://127.0.0.1:8080'


async def run_bus(url, bus_id, route):
    async with open_websocket_url(url) as ws:
        for coordinates in route:
            lat, lng = coordinates
            message = {'busId': bus_id, 'lat': lat, 'lng': lng, 'route': bus_id}
            await ws.send_message(json.dumps(message, ensure_ascii=False))
            await trio.sleep(DELAY)


async def main():
    try:
        async with trio.open_nursery() as nursery:
            for route in load_routes():
                nursery.start_soon(run_bus, URL, route['name'], route['coordinates'])

    except OSError as ose:
        print(f'Connection attempt failed: {ose}', file=sys.stderr)

    except KeyboardInterrupt:
        sys.exit()


if __name__ == '__main__':
    trio.run(main)
