import argparse
import asyncio
import datetime
import logging
import os

import aiofiles
from aiohttp import web

from functools import partial


logger = logging.getLogger('server')


async def archivate(request, path, delay, chunk_size=4096):
    archive_hash = request.match_info['archive_hash']
    path = os.path.join(path, archive_hash)

    if not os.path.exists(path):
        raise web.HTTPNotFound(text='The archive does not exist or has been deleted.')

    command = ['zip', '-jr', '-', path]
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    response = web.StreamResponse()
    response.enable_chunked_encoding()
    response.headers['Content-Disposition'] = 'attachment; filename="photos.zip"'
    await response.prepare(request)

    try:
        while True:
            stdout_chunk = await process.stdout.read(chunk_size)
            if not stdout_chunk:
                logger.info('Download complete!')
                break

            logger.info('Sending archive chunk...')
            await response.write(stdout_chunk)

            if delay:
                await asyncio.sleep(delay)

    except asyncio.CancelledError:
        logger.info('Download was interrupted.')
        raise

    finally:
        if process.returncode is None:
            process.kill()
            await process.communicate()

        response.force_close()
        return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


def get_arg_parser():
    parser = argparse.ArgumentParser(description="Micro service for downloading files")
    parser.add_argument('-l', '--logging', action='store_true')
    parser.add_argument('-d', '--delay', type=int, default=None)
    parser.add_argument('-p', '--path', default='test_photos')
    return parser


if __name__ == '__main__':
    args = get_arg_parser().parse_args()
    if args.logging:
        logging.basicConfig(level=logging.INFO)

    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', partial(archivate, path=args.path, delay=args.delay)),
    ])
    web.run_app(app)
