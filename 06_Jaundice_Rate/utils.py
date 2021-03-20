from bs4 import BeautifulSoup


def get_words_list(path):
    with open(path) as file:
        words = file.read()
    return words.split()


def get_article_title(html):
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.select_one('.article-header__title')
    if title:
        return title.text

    return soup.title.text if soup.title else None
