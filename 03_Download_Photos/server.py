import asyncio
import datetime
import aiofiles
from aiohttp import web


INTERVAL_SECS = 1
COMMAND = 'zip -r - test_photos/'


async def archivate(request, chunk_size=100):
    process = await asyncio.create_subprocess_shell(
        COMMAND,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    response = web.StreamResponse()
    response.headers['Content-Type'] = 'text/html'
    response.headers['Content-Disposition'] = 'attachment; filename="archive.zip"'
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
    archive_hash = '7kna'
    app.add_routes([
        web.get('/', handle_index_page),
        web.get(f'/archive/{archive_hash}/', archivate),
    ])
    web.run_app(app)
