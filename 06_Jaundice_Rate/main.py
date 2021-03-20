import asyncio
from enum import Enum

import aiohttp
import pymorphy2
from anyio import create_task_group, run

from adapters import SANITIZERS
from text_tools import split_by_words, calculate_jaundice_rate
from utils import get_words_list, get_article_title


TEST_ARTICLES = [
    'https://inosmi.ru/social/20210319/249367936q.html',
    'https://inosmi.ru/social/20210319/249367936.html',
    'https://inosmi.ru/politic/20210319/249371849.html',
    'https://inosmi.ru/politic/20210319/249368825.html',
    'https://inosmi.ru/politic/20210319/249369853.html',
    'https://inosmi.ru/politic/20210319/249370229.html',
    'https://inosmi.ru/politic/20210319/249372078.html',
]


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def process_article(session, url, morph, charged_words, results):
    try:
        html = await fetch(session, url)
    
        title = get_article_title(html)

        sanitizer = SANITIZERS['inosmi_ru']
        sanitized_text = sanitizer(html, plaintext=True)

        words = split_by_words(morph, sanitized_text)
        score = calculate_jaundice_rate(words, charged_words)

        words_count = len(words)

        results.append(
            {
                'title': title,
                'status': ProcessingStatus.OK.value,
                'score': score,
                'words_count': words_count,
            }
        )
    except aiohttp.ClientError:
        results.append(
            {
                'title': 'URL not exist',
                'status': ProcessingStatus.FETCH_ERROR.value,
                'score': None,
                'words_count': None,
            }
        )


def print_process_article_results(results):
    for result in results:
        print()
        print(f'Заголовок: {result["title"]}')
        print(f'Статус: {result["status"]}')
        print(f'Рейтинг: {result["score"]}')
        print(f'Слов в статье: {result["words_count"]}')
        print('===')


async def main():
    morph = pymorphy2.MorphAnalyzer()
    charged_words = get_words_list('negative_words.txt')

    process_article_results = []

    async with aiohttp.ClientSession() as session:
        async with create_task_group() as task_group:
            for url in TEST_ARTICLES:
                args = [
                    session,
                    url,
                    morph,
                    charged_words,
                    process_article_results
                ]
                await task_group.spawn(process_article, *args)

    print_process_article_results(process_article_results)


if __name__ == '__main__':
    run(main)
