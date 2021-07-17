import functools
import json

import trio
from trio_websocket import serve_websocket, ConnectionClosed


def get_bus_coordinates(path):
    with open(path) as file:
        bus_route = json.loads(file.read())
    return bus_route['coordinates']


async def send_coordinates(request, coordinates):
    ws = await request.accept()
    while True:
        try:
            for coordinate in coordinates:
                lat, lng = coordinate

                bus = {
                    "msgType": "Buses",
                    "buses": [
                        {"busId": "a134aa", "lat": lat, "lng": lng, "route": "670к"},
                    ]
                }

                await ws.send_message(json.dumps(bus))
                await trio.sleep(0.1)

        except ConnectionClosed:
            break


async def main():
    bus_coordinates = get_bus_coordinates('156.json')
    handle_coordinates = functools.partial(send_coordinates, coordinates=bus_coordinates)
    await serve_websocket(handle_coordinates, '127.0.0.1', 8000, ssl_context=None)


if __name__ == '__main__':
    trio.run(main)
