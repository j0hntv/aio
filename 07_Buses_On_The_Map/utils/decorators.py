import contextlib
from functools import wraps


def suppress(*exceptions):
    def wrap(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            with contextlib.suppress(exceptions):
                await func(*args, **kwargs)
        return inner
    return wrap
