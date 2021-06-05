import asyncio
import os

import aiohttp
import pymorphy2
from anyio import create_task_group, run
from bs4 import BeautifulSoup

from adapters.inosmi_ru import sanitize
from text_tools import split_by_words, calculate_jaundice_rate


CHARGED_DICT_PATH = 'charged_dict'
TEST_ARTICLES = [
    'https://inosmi.ru/politic/20210602/249840920.html',
    'https://inosmi.ru/social/20210603/249851439.html',
    'https://inosmi.ru/politic/20210603/249851956.html',
    'https://inosmi.ru/military/20210603/249853695.html',
    'https://inosmi.ru/politic/20210603/249852621.html',
    'https://inosmi.ru/military/20210603/249853929.html',
]


def get_charged_words(charged_dict_path):
    words = []

    for path in os.listdir(charged_dict_path):
        with open(os.path.join(charged_dict_path, path)) as file:
            words.extend(file.read().split('\n'))

    return words

def get_article_title(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.select_one('.article-header__title').text


async def process_article(session, morph, charged_words, url, results):
    html = await fetch(session, url)
    plaintext = sanitize(html, plaintext=True)
    title = get_article_title(html)
    splitted_by_words_text = split_by_words(morph, plaintext)

    score = calculate_jaundice_rate(splitted_by_words_text, charged_words)
    words_count = len(splitted_by_words_text)

    results.append(
        {
            'Заголовок': title,
            'Рейтинг': score,
            'Слов в статье': words_count,
        }
    )


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def main():
    url = 'https://inosmi.ru/politic/20210602/249840920.html'
    morph = pymorphy2.MorphAnalyzer()
    charged_words = get_charged_words(CHARGED_DICT_PATH)
    process_article_results = []

    async with aiohttp.ClientSession() as session:
        async with create_task_group() as task_group:
            for url in TEST_ARTICLES:
                await task_group.spawn(
                    process_article,
                    session,
                    morph,
                    charged_words,
                    url,
                    process_article_results
                )

    for result in process_article_results:
        for key, value in result.items():
            print(f'{key}: {value}')

        print('=====')


if __name__ == '__main__':
    run(main)
