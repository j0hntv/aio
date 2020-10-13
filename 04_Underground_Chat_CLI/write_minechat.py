import asyncio

import configargparse


def get_argument_parser():
    parser = configargparse.ArgParser()
    parser.add('--host', default='minechat.dvmn.org', env_var='HOST', help='Chat host')
    parser.add('--port', type=int, default=5050, env_var='WRITE_PORT', help='Chat port')
    parser.add('--hash', env_var='ACCOUNT_HASH', help='User account auth hash')
    parser.add('--message', help='Your message text')
    return parser


async def auth(writer, userhash):
    writer.write((userhash + '\n').encode())
    await writer.drain()


async def tcp_client(host, port):
    _, writer = await asyncio.open_connection(host, port)

    try:
        await auth(writer, ACCOUNT_HASH)

        writer.write(f'{MESSAGE}\n\n'.encode())
        await writer.drain()

    finally:
        writer.close()
        await writer.wait_closed()


if __name__ == '__main__':
    args = get_argument_parser().parse_args()

    HOST = args.host
    PORT = args.port
    ACCOUNT_HASH = args.hash
    MESSAGE = args.message

    asyncio.run(tcp_client(HOST, PORT))
