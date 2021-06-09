import json
from functools import partial

import pymorphy2
from aiohttp import web
from anyio import create_task_group

from article_tools import (
    get_charged_words,
    get_process_article_results
)

CHARGED_DICT_PATH = 'charged_dict'
TIMEOUT = 3


async def handle_article(request, morph, charged_words, json_encoder):
    urls = request.query.get('urls')

    if not urls:
        return web.json_response({'error': 'No url specified'}, dumps=json_encoder, status=400)
    
    urls = urls.split(',')
    process_article_results = []

    await get_process_article_results(urls, morph, charged_words, process_article_results)

    return web.json_response({'result': process_article_results}, dumps=json_encoder)


def main():
    morph = pymorphy2.MorphAnalyzer()
    charged_words = get_charged_words(CHARGED_DICT_PATH)

    json_encoder = partial(
        json.dumps,
        ensure_ascii=False,
        indent=4,
    )
    handle = partial(
        handle_article,
        morph=morph,
        charged_words=charged_words,
        json_encoder=json_encoder
    )

    app = web.Application()
    app.add_routes([web.get('/', handle)])
    web.run_app(app)


if __name__ == '__main__':
    main()
