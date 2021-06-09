import asyncio
import logging
import os
from contextlib import contextmanager
from enum import Enum
from time import monotonic

import aiohttp
from async_timeout import timeout
import pymorphy2
from anyio import create_task_group
from bs4 import BeautifulSoup

from adapters.inosmi_ru import sanitize
from adapters.exceptions import ArticleNotFound
from text_tools import split_by_words, calculate_jaundice_rate


CHARGED_DICT_PATH = 'charged_dict'
TIMEOUT = 3

logger = logging.getLogger('jaundice_rate')


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH ERROR'
    PARSING_ERROR = 'PARSING ERROR'
    TIMEOUT = 'TIMEOUT'

    def __str__(self):
        return self.value


def get_charged_words(charged_dict_path):
    words = []

    for path in os.listdir(charged_dict_path):
        with open(os.path.join(charged_dict_path, path)) as file:
            words.extend(file.read().split('\n'))

    return words


def get_title_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.find('title')

    return title.text if title else 'Unknown page title'


@contextmanager
def time_it():
    start_time = monotonic()
    yield
    end_time = monotonic()
    logger.info(f'Анализ закончен за {end_time - start_time:.2f} сек')


async def fetch(session, url):
    async with timeout(TIMEOUT):
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.text()


async def process_article(session, morph, charged_words, url, results):
    score, words_count = None, None
    try:
        html = await fetch(session, url)
        status = str(ProcessingStatus.OK)
        with time_it():
            title, plaintext = sanitize(html, plaintext=True)
            splitted_by_words_text = await split_by_words(morph, plaintext)
            score = calculate_jaundice_rate(splitted_by_words_text, charged_words)
            words_count = len(splitted_by_words_text)

    except aiohttp.ClientError:
        status = str(ProcessingStatus.FETCH_ERROR)
        title = 'URL not exist'

    except ArticleNotFound:
        status = str(ProcessingStatus.PARSING_ERROR)
        title = get_title_from_html(html)

    except asyncio.TimeoutError:
        status = str(ProcessingStatus.TIMEOUT)
        title = None

    results.append(
        {
            'title': title,
            'status': status,
            'score': score,
            'words_count': words_count,
        }
    )


async def get_process_article_results(urls, morph, charged_words, results):
    logging.basicConfig(level=logging.INFO)

    morph = pymorphy2.MorphAnalyzer()
    charged_words = get_charged_words(CHARGED_DICT_PATH)

    async with aiohttp.ClientSession() as session:
        async with create_task_group() as task_group:
            for url in urls:
                await task_group.spawn(
                    process_article,
                    session,
                    morph,
                    charged_words,
                    url,
                    results
                )
