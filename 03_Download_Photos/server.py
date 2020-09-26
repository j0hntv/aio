import asyncio
import datetime
import logging
import os

import aiofiles
from aiohttp import web


INTERVAL_SECS = 4
logger = logging.getLogger(__name__)


async def archivate(request, chunk_size=100):
    archive_hash = request.match_info['archive_hash']
    path = os.path.join('test_photos/', archive_hash)

    if not os.path.exists(path):
        raise web.HTTPNotFound(text='The archive does not exist or has been deleted.')

    command = ['zip', '-jr', '-', path]
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    response = web.StreamResponse()
    response.headers['Content-Disposition'] = 'attachment; filename="photos.zip"'
    await response.prepare(request)

    try:
        while True:
            stdout_chunk = await process.stdout.read(chunk_size*1000)
            if not stdout_chunk:
                logger.info('Download complete!')
                return response

            logger.info('Sending archive chunk...')
            await response.write(stdout_chunk)
            await asyncio.sleep(INTERVAL_SECS)

    except asyncio.CancelledError:
        logger.info('Download was interrupted.')
        raise

    finally:
        if process:
            process.kill()
        return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archivate),
    ])
    web.run_app(app)
