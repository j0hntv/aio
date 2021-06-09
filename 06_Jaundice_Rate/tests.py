import asyncio

import aiohttp
import pymorphy2

from article_tools import process_article, get_charged_words


async def run_process_article(url, status, http_timeout):
    morph = pymorphy2.MorphAnalyzer()
    charged_words = get_charged_words('charged_dict')
    results = []

    async with aiohttp.ClientSession() as session:
        await process_article(session, morph, charged_words, url, http_timeout, results)
        assert results[0]['status'] == status


def test_process_article_timeout():
    url = 'http://inosmi.ru/politic/20210602/249840920.html'
    status = 'TIMEOUT'
    asyncio.run(run_process_article(url, status, http_timeout=0))


def test_process_article_parsing_error():
    url = 'https://example.com/'
    status = 'PARSING ERROR'
    asyncio.run(run_process_article(url, status, http_timeout=5))


def test_process_article_fetch_error():
    url = 'https://xxx-yyy.zzz/'
    status = 'FETCH ERROR'
    asyncio.run(run_process_article(url, status, http_timeout=5))
