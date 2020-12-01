import asyncio
from dotenv import load_dotenv
import json
import logging

import configargparse


logger = logging.getLogger('Sender')


def get_argument_parser():
    parser = configargparse.ArgParser()
    parser.add('--host', env_var='HOST', help='Chat host')
    parser.add('-p', '--port', type=int, env_var='WRITE_PORT', help='Chat port')
    parser.add('-t', '--token', env_var='TOKEN', help='User account auth hash')
    parser.add('-m', '--message', help='Your message text')
    parser.add('-u', '--username', help='User name')
    return parser


def sanitize(text):
    return text.replace('\n', ' ')


async def register(reader, writer, username):
    await read_response(reader)
    await submit_message(writer, '\n')

    await read_response(reader)

    if username:
        await submit_message(writer, f'{sanitize(username)}\n')
    else:
        await submit_message(writer, '\n')

    response = await read_response(reader)
    register_info = json.loads(response)

    writer.close()
    await writer.wait_closed()
    
    return register_info


async def authorise(reader, writer, token):
    await read_response(reader)
    await submit_message(writer, f'{token}\n')
    response = await read_response(reader)
    authorise_info = json.loads(response)
    if not authorise_info:
        print('Неизвестный токен. Проверьте его или зарегистрируйте заново.')
        exit()

    return authorise_info


async def submit_message(writer, message):
    writer.write(message.encode())
    await writer.drain()


async def read_response(reader):
    response = await reader.readline()
    decoded_response = response.decode().strip()
    logger.info(decoded_response)
    return decoded_response


async def tcp_client(host, port, token=None, username=None, message=None):
    reader, writer = await asyncio.open_connection(host, port)

    try:
        if token:
            await authorise(reader, writer, token)
        else:
            register_info = await register(reader, writer, username)
            username = register_info['nickname']
            token = register_info['account_hash']
            reader, writer = await asyncio.open_connection(host, port)
            await authorise(reader, writer, token)

        if message:
            await submit_message(writer, f'{sanitize(MESSAGE)}\n\n')

    except Exception as error:
        print(error)

    finally:
        writer.close()
        await writer.wait_closed()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s %(message)s')

    load_dotenv()
    args = get_argument_parser().parse_args()

    HOST = args.host
    PORT = args.port
    TOKEN = args.token
    MESSAGE = args.message
    USERNAME = args.username

    print(f'\n{HOST=}, {PORT=}, {TOKEN=}, {USERNAME=}, {MESSAGE=}\n')

    asyncio.run(tcp_client(HOST, PORT, TOKEN, USERNAME, MESSAGE))
