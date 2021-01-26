import asyncio
import json
import socket
import tkinter as tk
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
        queues['register_info_queue'].put_nowait(register_info)

        return register_info


async def update_status(queues, user_label, token_label):
    register_info = await queues['register_info_queue'].get()

    username = register_info.get('nickname')
    token = register_info.get('account_hash')

    user_label['text'] = f'Username: {username}'
    token_label['text'] = f'Token: {token}'



def get_username(entry, queue):
    username = entry.get()
    queue['register_queue'].put_nowait(username)
    entry.delete(0, tk.END)


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

    user_label = tk.Label(width=50)
    user_label['text'] = 'Username:'

    token_label = tk.Label(width=50)
    token_label['text'] = 'Token:'

    register_button.bind('<Button-1>', lambda event: get_username(input_field, queues))

    input_frame.pack(ipadx=10, ipady=4, padx=10, pady=10)
    input_field.pack()
    register_button.pack()
    user_label.pack()
    token_label.pack()

    async with create_task_group() as task_group:
        await task_group.spawn(update_tk, root)
        await task_group.spawn(update_status, queues, user_label, token_label)


async def main():
    load_dotenv()
    args = get_argument_parser().parse_args()

    host = args.host
    port = args.write

    queues = {
        'register_queue': asyncio.Queue(),
        'register_info_queue': asyncio.Queue(),
    }

    async with create_task_group() as task_group:
        await task_group.spawn(draw, queues)
        await task_group.spawn(register, host, port, queues)


if __name__ == '__main__':
    run(main)
    