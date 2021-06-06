import asyncio
import os
from enum import Enum

import aiohttp
import pymorphy2
from anyio import create_task_group, run
from bs4 import BeautifulSoup

from adapters.inosmi_ru import sanitize
from text_tools import split_by_words, calculate_jaundice_rate


CHARGED_DICT_PATH = 'charged_dict'


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'


def get_charged_words(charged_dict_path):
    words = []

    for path in os.listdir(charged_dict_path):
        with open(os.path.join(charged_dict_path, path)) as file:
            words.extend(file.read().split('\n'))

    return words


def get_test_article_urls():
    with open('test_article_urls.txt') as file:
        return file.read().split('\n')


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def process_article(session, morph, charged_words, url, results):
    try:
        html = await fetch(session, url)
        status = ProcessingStatus.OK.value
        title, plaintext = sanitize(html, plaintext=True)
        splitted_by_words_text = split_by_words(morph, plaintext)
        score = calculate_jaundice_rate(splitted_by_words_text, charged_words)
        words_count = len(splitted_by_words_text)

    except aiohttp.ClientError:
        status = ProcessingStatus.FETCH_ERROR.value
        title = 'URL not exist'
        score = None
        words_count = None

    results.append(
        {
            'title': title,
            'status': status,
            'score': score,
            'words_count': words_count,
        }
    )


async def main():
    url = 'https://inosmi.ru/politic/20210602/249840920.html'
    morph = pymorphy2.MorphAnalyzer()
    charged_words = get_charged_words(CHARGED_DICT_PATH)
    process_article_results = []

    async with aiohttp.ClientSession() as session:
        async with create_task_group() as task_group:
            for url in get_test_article_urls():
                await task_group.spawn(
                    process_article,
                    session,
                    morph,
                    charged_words,
                    url,
                    process_article_results
                )

    for result in process_article_results:
        print(f'Заголовок: {result.get("title")}')
        print(f'Статус: {result.get("status")}')
        print(f'Рейтинг: {result.get("score")}')
        print(f'Слов в статье: {result.get("words_count")}')
        print('=====')


if __name__ == '__main__':
    run(main)
