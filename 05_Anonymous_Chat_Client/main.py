import asyncio
import time

import configargparse
from dotenv import load_dotenv

import gui


def get_argument_parser():
    parser = configargparse.ArgParser()
    parser.add('--host', default='minechat.dvmn.org', env_var='HOST', help='Host')
    parser.add('-l', '--listen', type=int, default=5000, env_var='LISTEN', help='Listen port')
    parser.add('-w', '--write', type=int, default=5050, env_var='WRITE', help='Write port')
    parser.add('-t', '--token', env_var='TOKEN', help='User account auth hash')
    parser.add('-u', '--username', help='User name')
    return parser


async def generate_msgs(queue: asyncio.Queue):
    while True:
        queue.put_nowait(time.time())
        await asyncio.sleep(1)


async def main():
    load_dotenv()
    args = get_argument_parser().parse_args()

    HOST = args.host
    LISTEN_PORT = args.listen
    WRITE_PORT = args.write
    TOKEN = args.token
    USERNAME = args.username

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    draw_coroutine = gui.draw(messages_queue, sending_queue, status_updates_queue)
    msg_coroutine = generate_msgs(messages_queue)

    await asyncio.gather(draw_coroutine, msg_coroutine)


if __name__ == '__main__':
    asyncio.run(main())
