import asyncio
import socket
from contextlib import asynccontextmanager

from gui import (
    ReadConnectionStateChanged,
    SendingConnectionStateChanged,
)


@asynccontextmanager
async def open_connection(host, port):
    writer = None
    try:
        reader, writer = await asyncio.open_connection(host, port)
        yield reader, writer

    except (ConnectionError, socket.gaierror, asyncio.TimeoutError):
        raise ConnectionError

    finally:
        if writer:
            writer.close()
            await writer.wait_closed()


def notify_connection_established(queues, status):
    reading_status = ReadConnectionStateChanged[status]
    sending_status = SendingConnectionStateChanged[status]
    queues['status_updates'].put_nowait(reading_status)
    queues['status_updates'].put_nowait(sending_status)


@asynccontextmanager
async def reconnect(host, port, queues):
    while True:
        notify_connection_established(queues, 'INITIATED')
        try:
            async with open_connection(host, port) as (reader, writer):
                notify_connection_established(queues, 'ESTABLISHED')
                yield reader, writer
        finally:
            notify_connection_established(queues, 'CLOSED')
