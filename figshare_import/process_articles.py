import pyld
import json

from pathlib import Path
from logging import getLogger
from datetime import datetime

from .utils import parse_name
from .conv import figshare_to_eml
from .defs import GROUP_ID, define_context


def write_article(article: dict, fmt: str, number: int):
    """
    Writes the article dict to a json file named as the list number of the article.
    """
    d = datetime.now().strftime('%Y-%m-%d')
    p = Path(f'~/figshare-jsonld/{d}').expanduser()
    if not p.exists():
        p.mkdir()
    with open(str(Path(p / f'{number}.{fmt}')), 'w') as f:
        json.dump(article, fp=f, indent=2)


def get_article_list(articles):
    """
    """
    L = getLogger(__name__)
    alist = None
    try:
        alist = articles.get('articles')
    except:
        L.info('articles object is not a dict. List, perhaps?')
    if alist:
        articles = alist
    else:
        if (type(articles) == list) and (len(articles) >= 1):
            L.info(f'articles object is a list of length {len(articles)}')
    L.info(f'Found {len(articles)} article records')
    return articles


def process_articles(articles: dict):
    """
    """
    L = getLogger(__name__)
    articles = get_article_list(articles)
    i = 0
    for article in articles:
        L.debug(f'Starting record {i}')
        write_article(article, fmt='json')
        eml = figshare_to_eml(article)
        write_article(eml, fmt='xml')
        i += 1

    return eml