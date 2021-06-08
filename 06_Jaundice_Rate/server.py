from aiohttp import web


async def handle(request):
    urls = request.query.get('urls')

    if urls:
        urls = urls.split(',')

    return web.json_response({'urls': urls})


def main():
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    web.run_app(app)


if __name__ == '__main__':
    main()
