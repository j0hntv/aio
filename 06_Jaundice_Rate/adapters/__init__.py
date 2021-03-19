from . import inosmi_ru
from .exceptions import ArticleNotFound

__all__ = ['SANITIZERS', 'ArticleNotFound']

SANITIZERS = {
    'inosmi_ru': inosmi_ru.sanitize,
}
