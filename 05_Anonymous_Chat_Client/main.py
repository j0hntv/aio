import asyncio
import json
import logging
import os
import socket
from contextlib import asynccontextmanager
from tkinter import messagebox

import aiofiles
from anyio import create_task_group, run, ExceptionGroup, sleep
from async_timeout import timeout
from dotenv import load_dotenv

import gui
from utils import get_argument_parser
from utils import setup_logger


PING_PONG_ERROR_TIMEOUT = 1
PING_PONG_DELAY = 2
CONNECTION_ERROR_TIMEOUT = 3

watchdog_logger = logging.getLogger('watchdog')


class InvalidToken(Exception):
    pass


@asynccontextmanager
async def open_connection(host, port, queues):
    writer = None

    while not writer:
        try:
            queues['status_updates'].put_nowait(gui.ReadConnectionStateChanged.INITIATED)
            queues['status_updates'].put_nowait(gui.SendingConnectionStateChanged.INITIATED)

            reader, writer = await asyncio.open_connection(host, port)

            queues['status_updates'].put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)
            queues['status_updates'].put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)

            yield reader, writer

        except (ConnectionError, socket.gaierror, asyncio.TimeoutError, ExceptionGroup):
            queues['watchdog'].put_nowait('No connection, try again...')
            await sleep(CONNECTION_ERROR_TIMEOUT)

        finally:
            if writer:
                writer.close()
                await writer.wait_closed()
                queues['status_updates'].put_nowait(gui.ReadConnectionStateChanged.CLOSED)
                queues['status_updates'].put_nowait(gui.SendingConnectionStateChanged.CLOSED)


def get_history(filepath):
    if os.path.exists(filepath):
        with open(filepath) as file:
            history = file.read()

        return history


def sanitize(text):
    return text.replace('\n', ' ')


def load_history(filepath, queue):
    history = get_history(filepath)
    if history:
        queue.put_nowait(history)
        queue.put_nowait('========***========\n')


async def watch_for_connection(queues):
    while True:
        event = await queues['watchdog'].get()
        watchdog_logger.info(event)


async def ping_pong(reader, writer, queues):
    while True:
        try:
            async with timeout(PING_PONG_ERROR_TIMEOUT) as cm:
                await reader.readline()
                writer.write('\n'.encode())
                await writer.drain()

            queues['watchdog'].put_nowait('Ping pong: connection is alive')
            await sleep(PING_PONG_DELAY)

        finally:
            if cm.expired:
                watchdog_logger.info(f'{PING_PONG_ERROR_TIMEOUT}s timeout is elapsed')


async def handle_connection(host, read_port, write_port, token, queues):
    while True:
        try:
            async with open_connection(host, write_port, queues) as (reader, writer):
                await authorise(reader, writer, token, queues)
                async with create_task_group() as task_group:
                    await task_group.spawn(send_msgs, reader, writer, token, queues)
                    await task_group.spawn(read_msgs, host, read_port, queues)
                    await task_group.spawn(ping_pong, reader, writer, queues)

        except InvalidToken:
            messagebox.showinfo('Неверный токен', 'Проверьте токен, сервер его не узнал.')
            exit()


async def request(writer, message):
    writer.write(message.encode())
    await writer.drain()


async def read_response(reader):
    response = await reader.readline()
    decoded_response = response.decode().strip()
    return decoded_response


async def authorise(reader, writer, token, queues):
    await read_response(reader)
    queues['watchdog'].put_nowait('Connection is alive. Prompt before auth')
    await request(writer, f'{token}\n')
    response = await read_response(reader)
    authorise_info = json.loads(response)
    nickname = authorise_info and authorise_info.get('nickname')

    if not nickname:
        raise InvalidToken

    queues['status_updates'].put_nowait(gui.NicknameReceived(nickname))
    queues['watchdog'].put_nowait('Connection is alive. Authorization done')

    return authorise_info


async def send_msgs(reader, writer, token, queues):
    while True:
        message = await queues['sending'].get()
        await request(writer, f'{sanitize(message)}\n\n')
        queues['watchdog'].put_nowait('Connection is alive. Message sent')


async def read_msgs(host, port, queues):
    async with open_connection(host, port, queues) as (reader, writer):
        while True:
            data = await reader.readline()
            message = data.decode().strip()
            queues['watchdog'].put_nowait('Connection is alive. New message in chat')
            queues['messages'].put_nowait(message)
            queues['saving'].put_nowait(message)


async def save_messages(filepath, queue):
    async with aiofiles.open(filepath, 'a') as file:
        while True:
            message = await queue.get()
            await file.write(f'{message}\n')
            await file.flush()


async def main():
    setup_logger(watchdog_logger)
    load_dotenv()
    args = get_argument_parser().parse_args()

    host = args.host
    listen_port = args.listen
    write_port = args.write
    token = args.token
    username = args.username
    historypath = args.path

    queues = {
        'messages': asyncio.Queue(),
        'sending': asyncio.Queue(),
        'status_updates': asyncio.Queue(),
        'saving': asyncio.Queue(),
        'watchdog': asyncio.Queue(),
    }

    load_history(historypath, queues['messages'])

    async with create_task_group() as task_group:
        await task_group.spawn(gui.draw, queues['messages'], queues['sending'], queues['status_updates'])
        await task_group.spawn(save_messages, historypath, queues['saving'])
        await task_group.spawn(handle_connection, host, listen_port, write_port, token, queues)
        await task_group.spawn(watch_for_connection, queues)


if __name__ == '__main__':
    try:
        run(main)
    except (gui.TkAppClosed, KeyboardInterrupt):
        pass
