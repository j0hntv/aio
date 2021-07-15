import json
import logging
from environs import Env
from functools import partial

import pymorphy2
from aiohttp import web

from article_tools import (
    get_charged_words,
    get_process_article_results
)


CHARGED_DICT_PATH = 'charged_dict'


def get_urls(request, max_urls_in_request):
    urls = request.query.get('urls')
    if not urls:
        message = 'No url specified'
        response = json.dumps({'error': message})
        raise web.HTTPBadRequest(text=response)

    urls = urls.split(',')
    if len(urls) > max_urls_in_request:
        message = f'Too many urls in request, should be {max_urls_in_request} or less'
        response = json.dumps({'error': message})
        raise web.HTTPBadRequest(text=response)

    return urls


async def handle_articles(request, morph, charged_words, json_encoder, max_urls_in_request, http_timeout):
    urls = get_urls(request, max_urls_in_request)
    article_results = await get_process_article_results(urls, morph, charged_words, http_timeout)

    return web.json_response({'result': article_results}, dumps=json_encoder)


def main():
    env = Env()
    env.read_env()
    
    max_urls_in_request = env.int('MAX_URLS_IN_REQUEST', 10)
    http_timeout = env.int('HTTP_TIMEOUT', 3)
    debug = env.bool('DEBUG', False)

    if debug:
        logging.basicConfig(level=logging.DEBUG)

    morph = pymorphy2.MorphAnalyzer()
    charged_words = get_charged_words(CHARGED_DICT_PATH)

    json_encoder = partial(
        json.dumps,
        ensure_ascii=False,
        indent=4,
    )
    handle = partial(
        handle_articles,
        morph=morph,
        charged_words=charged_words,
        json_encoder=json_encoder,
        max_urls_in_request=max_urls_in_request,
        http_timeout=http_timeout
    )

    app = web.Application()
    app.add_routes([web.get('/', handle)])
    web.run_app(app)


if __name__ == '__main__':
    main()
