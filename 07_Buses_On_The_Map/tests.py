import json

import trio
from trio_websocket import open_websocket_url


async def run_browser_wrong_data():
    async with open_websocket_url('ws://127.0.0.1:8080', ssl_context=None) as ws:
        messages = [' ', '[]']
        errors = ['value_error.jsondecode', 'value_error.missing']
        for message, error in zip(messages, errors):
            await ws.send_message(message)
            answer = json.loads(await ws.get_message())
            assert answer[0]['type'] == error


async def run_bus_wrong_data():
    async with open_websocket_url('ws://127.0.0.1:8000', ssl_context=None) as ws:
        messages = [' ', '[]']
        errors = ['value_error.jsondecode', 'value_error.missing']
        for message, error in zip(messages, errors):
            await ws.get_message()
            await ws.send_message(message)
            answer = json.loads(await ws.get_message())
            assert answer[0]['type'] == error


def test_broser_wrong_data():
    trio.run(run_browser_wrong_data)


def test_bus_wrong_data():
    trio.run(run_bus_wrong_data)
