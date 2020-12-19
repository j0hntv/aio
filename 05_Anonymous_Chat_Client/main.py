import asyncio
import gui
import time


async def generate_msgs(queue: asyncio.Queue):
    while True:
        queue.put_nowait(time.time())
        await asyncio.sleep(1)


async def main():
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    draw_coroutine = gui.draw(messages_queue, sending_queue, status_updates_queue)
    msg_coroutine = generate_msgs(messages_queue)

    await asyncio.gather(draw_coroutine, msg_coroutine)


if __name__ == '__main__':
    asyncio.run(main())
