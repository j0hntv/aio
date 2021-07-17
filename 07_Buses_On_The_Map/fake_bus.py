import json
import sys

import trio
from trio_websocket import open_websocket_url

from bus import get_bus_coordinates


async def main():
    coordinates = get_bus_coordinates('156.json')

    try:
        async with open_websocket_url('ws://127.0.0.1:8080') as ws:
            for coordinate in coordinates:
                lat, lng = coordinate
                message = {"busId": "156-0", "lat": lat, "lng": lng, "route": "156"}
                await ws.send_message(json.dumps(message))
                await trio.sleep(0.5)

    except OSError as ose:
        print(f'Connection attempt failed: {ose}', file=sys.stderr)

    except KeyboardInterrupt:
        sys.exit()


if __name__ == '__main__':
    trio.run(main)
