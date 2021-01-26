import logging

import configargparse


def get_argument_parser():
    parser = configargparse.ArgParser()
    parser.add('--host', default='minechat.dvmn.org', env_var='HOST', help='Host')
    parser.add('-l', '--listen', type=int, default=5000, env_var='LISTEN', help='Listen port')
    parser.add('-w', '--write', type=int, default=5050, env_var='WRITE', help='Write port')
    parser.add('-t', '--token', env_var='TOKEN', help='User account auth hash')
    parser.add('-p', '--path', default='history.log', env_var='HISTORYPATH', help='Filepath for saving messages')
    parser.add('-d', '--debug', default=False, env_var='DEBUG', help='Debug mode')
    return parser


def setup_logger(logger, fmt='[%(created)d] %(message)s', debug=False):
    logger.setLevel(logging.DEBUG if debug else logging.ERROR)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(fmt)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
