import asyncio
import json
import sys
import textwrap
import tkinter as tk
from tkinter import messagebox

from anyio import create_task_group, run, sleep
from dotenv import load_dotenv

from gui import TkAppClosed
from download_tools import open_connection
from utils import (
    get_argument_parser,
    submit_message,
    read_response,
)


def get_username(entry, queue):
    username = entry.get()
    queue['register_queue'].put_nowait(username)
    entry.delete(0, tk.END)


def save_token(path, token):
    with open(path, 'w') as file:
        file.write(f'MINECHAT_TOKEN={token}\n')


async def register(host, port, queues):
    username = await queues['register_queue'].get()

    async with open_connection(host, port) as (reader, writer):
        await read_response(reader)
        await submit_message(writer, '\n', sanitize=False, add_line_break=False)

        await read_response(reader)

        if username:
            await submit_message(writer, username)
        else:
            await submit_message(writer, '\n', sanitize=False, add_line_break=False)

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
    write_port = args.write_port

    queues = {
        'register_queue': asyncio.Queue(),
    }

    try:
        async with create_task_group() as task_group:
            await task_group.spawn(draw, queues)
            await task_group.spawn(register, host, write_port, queues)
    except ConnectionError:
        error_message = textwrap.dedent(
            '''\
            Прибежали в избу дети,
            Второпях зовут отца:
            Папа, папа, нету сети,
            И не подключаецца!'''
        )
        messagebox.showerror('Ошибка подключения', error_message)
        sys.exit()


if __name__ == '__main__':
    try:
        run(main)
    except (TkAppClosed, KeyboardInterrupt):
        sys.exit()
