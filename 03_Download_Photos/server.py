import asyncio
import datetime
import os

import aiofiles
from aiohttp import web


INTERVAL_SECS = 0.1
COMMAND = 'zip -rj - '


async def archivate(request, chunk_size=100):
    archive_hash = request.match_info['archive_hash']
    path = os.path.join('test_photos/', archive_hash)

    if not os.path.exists(path):
        raise web.HTTPNotFound(text='The archive does not exist or has been deleted.')

    process = await asyncio.create_subprocess_shell(
        COMMAND + path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    response = web.StreamResponse()
    response.headers['Content-Disposition'] = 'attachment; filename="photos.zip"'
    await response.prepare(request)

    while True:
        stdout_chunk = await process.stdout.read(chunk_size*1000)
        if not stdout_chunk:
            return response

        await response.write(stdout_chunk)
        await asyncio.sleep(INTERVAL_SECS)


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archivate),
    ])
    web.run_app(app)
