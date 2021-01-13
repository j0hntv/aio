import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from tkinter import messagebox

import aiofiles
import configargparse
from async_timeout import timeout
from dotenv import load_dotenv

import gui


TIMEOUT = 2

watchdog_logger = logging.getLogger('watchdog')


class InvalidToken(Exception):
    pass


def setup_logger(logger, fmt='[%(created)d] %(message)s'):
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(fmt)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


@asynccontextmanager
async def open_connection(host, port):
    try:
        reader, writer = await asyncio.open_connection(host, port)
        yield reader, writer
    finally:
        writer.close()
        await writer.wait_closed()


def get_argument_parser():
    parser = configargparse.ArgParser()
    parser.add('--host', default='minechat.dvmn.org', env_var='HOST', help='Host')
    parser.add('-l', '--listen', type=int, default=5000, env_var='LISTEN', help='Listen port')
    parser.add('-w', '--write', type=int, default=5050, env_var='WRITE', help='Write port')
    parser.add('-t', '--token', env_var='TOKEN', help='User account auth hash')
    parser.add('-p', '--path', default='history.log', env_var='HISTORYPATH', help='Filepath for saving messages')
    parser.add('-u', '--username', help='User name')
    return parser


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
        try:
            async with timeout(TIMEOUT) as cm:
                event = await queues['watchdog'].get()
                watchdog_logger.info(event)
        except asyncio.TimeoutError:
            if cm.expired:
                watchdog_logger.info(f'{TIMEOUT}s timeout is elapsed')


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

    queues['status_updates'].put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)
    queues['status_updates'].put_nowait(gui.NicknameReceived(nickname))
    queues['watchdog'].put_nowait('Connection is alive. Authorization done')

    return authorise_info


async def send_msgs(host, port, token, queues):
    async with open_connection(host, port) as (reader, writer):
        try:
            await authorise(reader, writer, token, queues)
        except InvalidToken:
            messagebox.showinfo('Неверный токен', 'Проверьте токен, сервер его не узнал.')
            exit()

        while True:
            message = await queues['sending'].get()
            await request(writer, f'{sanitize(message)}\n\n')
            queues['watchdog'].put_nowait('Connection is alive. Message sent')


async def read_msgs(host, port, queues):
    async with open_connection(host, port) as (reader, writer):
        queues['status_updates'].put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)
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
    load_dotenv()
    args = get_argument_parser().parse_args()

    HOST = args.host
    LISTEN_PORT = args.listen
    WRITE_PORT = args.write
    TOKEN = args.token
    USERNAME = args.username
    HISTORYPATH = args.path

    queues = {
        'messages': asyncio.Queue(),
        'sending': asyncio.Queue(),
        'status_updates': asyncio.Queue(),
        'saving': asyncio.Queue(),
        'watchdog': asyncio.Queue(),
    }

    queues['status_updates'].put_nowait(gui.ReadConnectionStateChanged.INITIATED)
    queues['status_updates'].put_nowait(gui.SendingConnectionStateChanged.INITIATED)

    load_history(HISTORYPATH, queues['messages'])

    draw_coroutine = gui.draw(queues['messages'], queues['sending'], queues['status_updates'])
    read_msg_coroutine = read_msgs(HOST, LISTEN_PORT, queues)
    send_msg_coroutine = send_msgs(HOST, WRITE_PORT, TOKEN, queues)
    save_messages_coroutine = save_messages(HISTORYPATH, queues['saving'])
    watch_for_connection_coroutine = watch_for_connection(queues)

    coroutines = [
        draw_coroutine,
        read_msg_coroutine,
        send_msg_coroutine,
        save_messages_coroutine,
        watch_for_connection_coroutine,
    ]

    await asyncio.gather(*coroutines, return_exceptions=True)


if __name__ == '__main__':
    setup_logger(watchdog_logger)
    asyncio.run(main())
