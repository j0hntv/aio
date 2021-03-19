import asyncio

import aiohttp
import pymorphy2
from anyio import create_task_group, run

from adapters import SANITIZERS
from text_tools import split_by_words, calculate_jaundice_rate
from utils import get_words_list, get_article_title


TEST_ARTICLES = [
    'https://inosmi.ru/social/20210319/249367936.html',
    'https://inosmi.ru/politic/20210319/249371849.html',
    'https://inosmi.ru/politic/20210319/249368825.html',
    'https://inosmi.ru/politic/20210319/249369853.html',
    'https://inosmi.ru/politic/20210319/249370229.html',
    'https://inosmi.ru/politic/20210319/249372078.html',
]


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def process_article(session, url, morph, charged_words):
    html = await fetch(session, url)
    title = get_article_title(html)

    sanitizer = SANITIZERS['inosmi_ru']
    sanitized_text = sanitizer(html, plaintext=True)

    words = split_by_words(morph, sanitized_text)
    score = calculate_jaundice_rate(words, charged_words)

    words_count = len(words)

    print('Заголовок:', title)
    print('Рейтинг:', score)
    print('Слов в статье:', words_count)
    print('===')


async def main():
    morph = pymorphy2.MorphAnalyzer()
    charged_words = get_words_list('negative_words.txt')
    
    async with aiohttp.ClientSession() as session:
        async with create_task_group() as task_group:
            for url in TEST_ARTICLES:
                await task_group.spawn(process_article, session, url, morph, charged_words)


if __name__ == '__main__':
    run(main)
