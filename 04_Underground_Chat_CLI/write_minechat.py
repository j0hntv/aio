import asyncio
import json
import logging

import configargparse


logger = logging.getLogger('Sender')


def get_argument_parser():
    parser = configargparse.ArgParser()
    parser.add('--host', env_var='HOST', help='Chat host')
    parser.add('--port', type=int, env_var='WRITE_PORT', help='Chat port')
    parser.add('--hash', env_var='ACCOUNT_HASH', help='User account auth hash')
    parser.add('--message', help='Your message text')
    return parser


async def register(reader, writer, username):
    logger.info((await reader.readline()).decode().strip())
    writer.write('\n'.encode())
    logger.info((await reader.readline()).decode().strip())
    writer.write(f'{username}\n'.encode())

    response = await reader.readline()
    await writer.drain()

    register_info = json.loads(response.decode())
    logger.info(register_info)

    writer.close()
    await writer.wait_closed()
    
    return register_info


async def auth(reader, writer, hash):
    logger.info((await reader.readline()).decode().strip())
    writer.write((hash + '\n').encode())
    await writer.drain()

    response = await reader.readline()
    auth_info = json.loads(response.decode())
    logger.info(auth_info)
    if not auth_info:
        print('Неизвестный токен. Проверьте его или зарегистрируйте заново.')
        exit()

    return auth_info


async def send_message(reader, writer, message):
    writer.write(f'{message}\n\n'.encode())
    await writer.drain()


async def tcp_client(host, port):
    reader, writer = await asyncio.open_connection(host, port)

    try:
        await auth(reader, writer, ACCOUNT_HASH)
        await send_message(reader, writer, MESSAGE)

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

    print(f'\n{HOST=}, {PORT=}, {ACCOUNT_HASH=}, {MESSAGE=}\n')

    asyncio.run(tcp_client(HOST, PORT))
