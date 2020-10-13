import asyncio
from datetime import datetime

import aiofiles
import configargparse


def get_argument_parser():
    parser = configargparse.ArgParser()
    parser.add('--host', default='minechat.dvmn.org', env_var='HOST', help='Chat host')
    parser.add('--port', type=int, default=5000, env_var='LISTEN_PORT', help='Chat port')
    parser.add('--history', default='messages.log', env_var='HISTORY_PATH', help='Path to the message history file')
    return parser


async def save_message(path, message):
    async with aiofiles.open(path, 'a') as file:
        await file.write(message)


async def tcp_client(host, port):
    reader, writer = await asyncio.open_connection(host, port)

    try:
        while True:
            data = await reader.readline()
            time = datetime.now().strftime('[%Y.%m.%d %H:%M]')
            message = f'{time} {data.decode()}'
            print(message.strip())
            await save_message(HISTORY_PATH, message)

    except KeyboardInterrupt:
        print('[*] Exit.')

    finally:
        writer.close()
        await writer.wait_closed()


if __name__ == '__main__':
    args = get_argument_parser().parse_args()

    HOST = args.host
    PORT = args.port
    HISTORY_PATH = args.history

    asyncio.run(tcp_client(HOST, PORT))
