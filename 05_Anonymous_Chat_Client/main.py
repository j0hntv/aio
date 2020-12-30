import asyncio
import os
from contextlib import asynccontextmanager

import aiofiles
import configargparse
from dotenv import load_dotenv

import gui


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


def load_history(filepath, queue):
    history = get_history(filepath)
    if history:
        queue.put_nowait(history)
        queue.put_nowait('========***========\n')


async def read_msgs(host, port, queues):
    async with open_connection(host, port) as (reader, writer):
        while True:
            data = await reader.readline()
            message = data.decode().strip()
            queues['messages'].put_nowait(message)
            queues['saving'].put_nowait(message)


async def send_msgs(host, port, queue):
    while True:
        message = await queue.get()
        print(message)


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
    }

    load_history(HISTORYPATH, queues['messages'])

    draw_coroutine = gui.draw(queues['messages'], queues['sending'], queues['status_updates'])
    read_msg_coroutine = read_msgs(HOST, LISTEN_PORT, queues)
    send_msg_coroutine = send_msgs(HOST, WRITE_PORT, queues['sending'])
    save_messages_coroutine = save_messages(HISTORYPATH, queues['saving'])

    await asyncio.gather(draw_coroutine, read_msg_coroutine, send_msg_coroutine, save_messages_coroutine)


if __name__ == '__main__':
    asyncio.run(main())
