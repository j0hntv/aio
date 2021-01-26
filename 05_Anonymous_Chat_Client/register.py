import asyncio
import json
import socket
import sys
import tkinter as tk
from tkinter import messagebox
from contextlib import asynccontextmanager

from anyio import create_task_group, run, sleep
from dotenv import load_dotenv

from gui import TkAppClosed
from utils import get_argument_parser


@asynccontextmanager
async def open_connection(host, port):
    writer = None
    try:
        reader, writer = await asyncio.open_connection(host, port)
        yield reader, writer

    finally:
        if writer:
            writer.close()
            await writer.wait_closed()


async def submit_message(writer, message):
    writer.write(message.encode())
    await writer.drain()


async def read_response(reader):
    response = await reader.readline()
    decoded_response = response.decode().strip()
    return decoded_response


def get_username(entry, queue):
    username = entry.get()
    queue['register_queue'].put_nowait(username)
    entry.delete(0, tk.END)


def save_token(path, token):
    with open(path, 'w') as file:
        file.write(f'TOKEN={token}\n')


async def register(host, port, queues):
    username = await queues['register_queue'].get()

    async with open_connection(host, port) as (reader, writer):
        await read_response(reader)
        await submit_message(writer, '\n')

        await read_response(reader)

        if username:
            await submit_message(writer, f'{username}\n')
        else:
            await submit_message(writer, '\n')

        response = await read_response(reader)

    register_info = json.loads(response)

    token = register_info.get('account_hash')
    save_token('.env', token)

    username = register_info.get('nickname')
    message = f'Зарегистрирован аккаунт:\n{username}'
    messagebox.showinfo('Инфо', message)
    sys.exit()


async def update_tk(root_frame, interval=1 / 120):
    while True:
        try:
            root_frame.update()
        except tk.TclError:
            # if application has been destroyed/closed
            raise TkAppClosed()
        await sleep(interval)


async def draw(queues):
    root = tk.Tk()
    root.title('Регистрация нового пользователя')

    input_frame = tk.LabelFrame(text='Имя пользователя')

    input_field = tk.Entry(input_frame, width=30, justify='center', font='Arial 18')
    input_field.bind('<Return>', lambda event: get_username(input_field, queues))

    register_button = tk.Button(text='Регистрация')
    register_button.bind('<Button-1>', lambda event: get_username(input_field, queues))

    input_frame.pack(ipadx=10, ipady=4, padx=10, pady=5)
    input_field.pack()
    register_button.pack(pady=10)

    await update_tk(root)


async def main():
    load_dotenv()
    args = get_argument_parser().parse_args()

    host = args.host
    port = args.write

    queues = {
        'register_queue': asyncio.Queue(),
    }

    async with create_task_group() as task_group:
        await task_group.spawn(draw, queues)
        await task_group.spawn(register, host, port, queues)


if __name__ == '__main__':
    try:
        run(main)
    except (TkAppClosed, KeyboardInterrupt):
        sys.exit()
