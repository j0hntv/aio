import asyncio
import logging

import configargparse


logger = logging.getLogger('Sender')


def get_argument_parser():
    parser = configargparse.ArgParser()
    parser.add('--host', default='minechat.dvmn.org', env_var='HOST', help='Chat host')
    parser.add('--port', type=int, default=5050, env_var='WRITE_PORT', help='Chat port')
    parser.add('--hash', env_var='ACCOUNT_HASH', help='User account auth hash')
    parser.add('--message', help='Your message text')
    return parser


async def auth(writer, hash):
    writer.write((hash + '\n').encode())
    logger.info(hash)
    await writer.drain()


async def log(reader):
    data = await reader.readline()
    logger.info(data.decode().strip())


async def tcp_client(host, port):
    reader, writer = await asyncio.open_connection(host, port)

    try:
        await log(reader)
        await auth(writer, ACCOUNT_HASH)
        await log(reader)
        
        writer.write(f'{MESSAGE}\n\n'.encode())
        await writer.drain()
        await log(reader)

    finally:
        writer.close()
        await writer.wait_closed()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s %(message)s')
    args = get_argument_parser().parse_args()

    HOST = args.host
    PORT = args.port
    ACCOUNT_HASH = args.hash
    MESSAGE = args.message

    asyncio.run(tcp_client(HOST, PORT))
