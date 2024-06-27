import pyld
import json

from pathlib import Path
from logging import getLogger

def load_xwalk(loc=Path('~/bin/figshare-import/figshare_import/manifest/figshare.jsonld').expanduser()):
    """
    """
    with open(loc, 'r') as f:
        return json.load(f)

def create_eml(article: dict, xwalk: dict):
    """
    """
    L = getLogger(__name__)
    compacted = pyld.jsonld.compact(article, ctx=xwalk)
    L.debug(f'Compacted article:\n{compacted}')
    expanded = pyld.jsonld.expand(compacted, ctx=xwalk)
    pyld.jsonld.flatten()
    L.debug(f'Expanded article:\n{expanded}')
    return expanded