import logging

import configargparse


def get_argument_parser():
    parser = configargparse.ArgParser()
    parser.add('--host', default='minechat.dvmn.org', env_var='HOST', help='Host')
    parser.add('-l', '--listen_port', type=int, default=5000, env_var='LISTEN_PORT', help='Listen port')
    parser.add('-w', '--write_port', type=int, default=5050, env_var='WRITE_PORT', help='Write port')
    parser.add('-t', '--token', env_var='MINECHAT_TOKEN', help='User account auth hash')
    parser.add('-p', '--path', default='history.log', env_var='HISTORYPATH', help='Filepath for saving messages')
    parser.add('-d', '--debug', env_var='DEBUG', help='Debug mode', action='store_true')
    return parser


def setup_logger(logger, fmt='[%(created)d] %(message)s', debug=False):
    logger.setLevel(logging.DEBUG if debug else logging.ERROR)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(fmt)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def sanitize_text(text):
    return text.replace('\n', ' ')


async def submit_message(writer, message, sanitize=True, add_line_break=True):
    if sanitize:
        message = sanitize_text(message)

    if add_line_break:
        message += '\n\n'
    
    writer.write(message.encode())

    await writer.drain()


async def read_response(reader):
    response = await reader.readline()
    decoded_response = response.decode().strip()
    return decoded_response
