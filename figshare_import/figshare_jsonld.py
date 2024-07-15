import pyld
import json

from pathlib import Path
from logging import getLogger
from datetime import datetime

from .parse_names import parse_name
from .conv import frame
from .defs import GROUP_ID, define_context


def write_jld(article: dict, fmt: str, number: int):
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


def process(article: dict, xwalk: dict=define_context()):
    """
    """
    a = 0
    for author in article['authors']:
        if not (article['authors'][a]['url_name'] == '_'):
            article['authors'][a]['url'] = f'https://figshare.com/authors/{author["url_name"]}/{author["id"]}'
        article['authors'][a]['id'] = str(author['id'])
        if not (article['authors'][a]['orcid_id'] == ''):
            orcid_url = f'http://orcid.org/{author["orcid_id"]}'
            article['authors'][a]['orcid_id'] = orcid_url
            article['authors'][a]['url'] = orcid_url
        given, family = parse_name(fullname=author['full_name'])
        article['authors'][a]['given_name'] = given
        article['authors'][a]['family_name'] = family
        article['authors'][a]['@type'] = 'Person'
        a += 1
    fi = 0
    for f in article['files']:
        article['files'][fi]['size'] = str(f['size'])
        article['files'][fi]['id'] = str(f['id'])
        fi += 1
    ci = 0
    for c in article['categories']:
        article['categories'][ci]['id'] = str(c['id'])
        ci += 1
    article['size'] = str(article['size'])
    article['id'] = str(article['id'])
    article['identifier'] = {
        "@id": f"https://doi.org/{article['doi']}",
        "@type": "PropertyValue",
        "propertyID": "https://registry.identifiers.org/registry/doi",
        "value": f"doi:{article['doi']}",
        "url": f"https://doi.org/{article['doi']}",
    }
    article['license']['id'] = article['license']['url']
    try:
        article['Organization'] = GROUP_ID[article['group_id']]
    except:
        article['Organization'] = "Smithsonian Research Data"
    article['defined_type_name'] = "Dataset"
    context = xwalk.get('@context')
    if not context:
        context = xwalk
    return frame(article, context=context)

def process_articles(articles: dict):
    """
    """
    L = getLogger(__name__)
    articles = get_article_list(articles)
    i = 0
    for article in articles:
        L.debug(f'Starting record {i}')
        #write_jld(article, fmt='json')
        so = process(article)
        #write_jld(so, fmt='jsonld')
        i += 1

    return so