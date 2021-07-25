import contextlib
from functools import wraps

from trio import sleep
from trio_websocket import ConnectionClosed, HandshakeError


def suppress(*exceptions):
    def wrap(async_function):
        @wraps(async_function)
        async def inner(*args, **kwargs):
            with contextlib.suppress(exceptions):
                await async_function(*args, **kwargs)
        return inner
    return wrap


def relaunch_on_disconnect(logger=None, delay=1):
    def wrap(async_function):
        @wraps(async_function)
        async def inner(*args, **kwargs):
            while True:
                try:
                    await async_function(*args, **kwargs)
                except (ConnectionClosed, HandshakeError) as error:
                    if logger:
                        logger.error(f'Connection lost. Try to reconnect in {delay} sec.')
                    await sleep(delay)
        return inner
    return wrap
