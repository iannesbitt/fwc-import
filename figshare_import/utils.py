import json
import re
from pygeodesy.namedTuples import LatLon3Tuple
from logging import getLogger
from d1_client.mnclient_2_0 import MemberNodeClient_2_0

from pathlib import Path
from logging import getLogger
from datetime import datetime

from .conv import figshare_to_eml
from .defs import GROUP_ID, CN_URL, CONFIG_LOC, CONFIG
from .run_data_upload import get_doipath


def get_token():
    """
    Get the DataONE token from the token file.
    Paste your auth token into './.d1_token'.

    :return: The DataONE token.
    :rtype: str
    """
    # Set the D1 token
    with open(Path(CONFIG_LOC / '.d1_token'), 'r') as tf:
        return tf.read().split('\n')[0]


def get_config():
    """
    Config values that are not the d1 token go in 'config.json'.

    :return: The ORCID, node identifier, Member Node URL, and metadata JSON file.
    :rtype: tuple
    """
    global DATA_ROOT
    global CN_URL
    global CONFIG
    # Set your ORCID
    CONFIG = CONFIG_LOC.joinpath('config.json')
    with open(CONFIG, 'r') as lc:
        config = json.load(lc)
    # set the data root and CN URL
    DATA_ROOT = Path(config['data_root'])
    CN_URL = config['cnurl'] if config.get('cnurl') else CN_URL
    return config['rightsholder_orcid'], config['nodeid'], config['mnurl'], str(Path(config['metadata_json']).expanduser())


def parse_name(fullname: str):
    """
    Parse full names into given and family designations.
    """
    given, family = None, None
    if ', ' in fullname:
        [family, given] = fullname.title().split(', ')[:2]
    if (given == None) and (family == None):
        for q in [' del ', ' van ']:
            if q in fullname.lower():
                [given, family] = fullname.lower().split(q)
                given = given.title()
                family = f'{q.strip()}{family.title()}'
    if (given == None) and (family == None):
        nlist = fullname.title().split()
        family = nlist[-1]
        if len(nlist) >= 2:
            given = nlist[0]
            for i in range(1, len(nlist)-1):
                given = f'{given} {nlist[i]}'
    if (not given) or (not family):
        L = getLogger()
        L.warning(f'Could not parse name "{fullname}". Result of given name: "{given}" Family name: "{family}"')
    return given, family


def dms_to_decimal(degrees, minutes, seconds, direction):
    decimal = float(degrees) + float(minutes)/60 + float(seconds)/3600
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal


def get_lat_lon(desc: str):
    """
    Parse latitude and longitude from description and convert to decimal degrees.
    Return all pairs found as a list of LatLon3Tuple objects.
    """
    patterns = [
        r'([+-]?\d+(\.\d+)?)°?\s*,?\s*([+-]?\d+(\.\d+)?)°?',  # 8.994410°, - 79.543000°
        r'([+-]?\d+(\.\d+)?)°?\s*([NS]),?\s*([+-]?\d+(\.\d+)?)°?\s*([EW])',  # 8.910718°N, -79.528919°
        r'(\d+)°\s*(\d+(\.\d+)?)\'?\s*([NS]),?\s*(\d+)°\s*(\d+(\.\d+)?)\'?\s*([EW])',  # 7° 38.422'N, 81° 42.079'W
        r'(\d+)°\s*(\d+)\'\s*(\d+(\.\d+)?)\"?\s*([NS]),?\s*(\d+)°\s*(\d+)\'\s*(\d+(\.\d+)?)\"?\s*([EW])',  # 9°9'42.36"N, 79°50'15.67"W
        r'(\d+)°\s*(\d+)′\s*([NS])\s*latitude,\s*(\d+)°\s*(\d+)′\s*([EW])\s*longitude',  # 9°41′ S latitude, 76°24′ W longitude
        r'(\d+)°\s*(\d+(\.\d+)?)\'?\s*([NS])\s+(\d+)°\s*(\d+(\.\d+)?)\'?\s*([EW])'  # 8° 38.743'N    79° 2.887'W
    ]
    
    latlon = []
    
    for pattern in patterns:
        matches = re.findall(pattern, desc)
        for match in matches:
            if len(match) == 4:
                # Decimal degrees format
                lat = float(match[0])
                lon = float(match[2])
            elif len(match) == 6:
                # Decimal degrees with direction
                lat = float(match[0]) * (-1 if match[2] == 'S' else 1)
                lon = float(match[3]) * (-1 if match[5] == 'W' else 1)
            elif len(match) == 8:
                # Degrees and decimal minutes with direction
                lat = dms_to_decimal(match[0], match[1], 0, match[3])
                lon = dms_to_decimal(match[4], match[5], 0, match[7])
            elif len(match) == 10:
                # Degrees, minutes, and seconds with direction
                lat = dms_to_decimal(match[0], match[1], match[2], match[4])
                lon = dms_to_decimal(match[5], match[6], match[7], match[9])
            latlon.append(LatLon3Tuple(lat, lon, 0))
    return latlon


def pathify(title: str):
    """
    Convert a title to a file path.

    :param title: The title to convert.
    :type title: str
    :return: The pathified title.
    :rtype: str
    """
    return re.sub(r'[^\w\s]', '', title).replace(' ', '_')[:48]


def write_article(article: dict, doi: str, title: str, fmt: str):
    """
    Writes the article dictionary to a file.

    :param article: The article data to write.
    :type article: dict
    :param path: The format to write the article in (e.g., 'json', 'xml').
    :type path: Path
    """
    doipath = get_doipath(doi)
    path = Path(doipath / pathify(title) + f".{fmt}")
    with open(str(Path(path)), 'w') as f:
        if fmt == 'json':
            json.dump(article, fp=f, indent=2)
        elif fmt == 'xml':
            f.write(article)


def get_article_list(articles):
    """
    Retrieves the list of articles from the provided data.

    :param articles: The data containing articles.
    :type articles: dict or list
    :return: The list of articles.
    :rtype: list
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
    This function performs three actions:

    1. Writes the original Figshare metadata to files in JSON format.
    2. Converts the Figshare metadata to EML-formatted strings.
    3. Writes the EML to XML.
    Archives Figshare articles by writing them to files in different formats.

    :param articles: The data containing articles.
    :type articles: dict
    :return: A list of processed articles in EML format.
    :rtype: dict
    """
    L = getLogger(__name__)
    articles = get_article_list(articles)
    eml_list = []
    i = 0
    for article in articles:
        L.debug(f'Starting record {i}')
        write_article(article, fmt='json', doi=article.get('doi'), title=article.get('title'))
        eml = figshare_to_eml(article)
        write_article(eml, fmt='xml', doi=article.get('doi'), title=article.get('title'))
        eml_list.append(eml)
        i += 1

    return eml_list


def get_d1_ids(filedict: dict, client: MemberNodeClient_2_0):
    """
    Retrieve DataONE object identifiers for hashed files in a file dictionary.

    :param dict filedict: A dictionary containing file information.
    :param MemberNodeClient_2_0 client: A DataONE MemberNodeClient_2_0 object.
    :return: A dictionary with updated file information including identifiers, formatIds, and URLs.
    :rtype: dict
    """
    L = getLogger(__name__)
    sep = '' if CN_URL.endswith('/') else '/'
    try:
        object_list = client.listObjects(start=0, count=1)
        tot = object_list.total
        L.info(f'Total number of objects in MN {client.base_url}: {tot}')
        object_list_list = []
        object_list_list.append(client.listObjects(start=0, count=tot))
        if not (object_list_list[0].total == tot):
            L.info(f'Got {object_list_list[0].total} of {tot} objects, requesting the rest...')
            object_list_list.append([client.listObjects(start=i, count=tot) for i in range(object_list_list[0].count, tot, object_list_list[0].count)])
            L.info('Done.')
    except Exception as e:
        L.error(f"Failed to retrieve object list from DataONE: {e}")
        return filedict
    # Create a dictionary to map MD5 sums to identifiers, formatIds, and URLs
    obj_info = {}
    for object_list in object_list_list:
        for obj in object_list.objectInfo:
            obj_info[obj.checksum.value()] = {
                'identifier': obj.identifier.value(),
                'formatId': obj.formatId,
                'url': f"{CN_URL}{sep}v2/resolve/{obj.identifier.value()}"
            }
    # Update the file info dictionary
    for doi, files in filedict.items():
        for md5, file_info in files.items():
            if md5 in obj_info:
                file_info['identifier'] = obj_info[md5]['identifier']
                file_info['formatId'] = obj_info[md5]['formatId']
                file_info['url'] = obj_info[md5]['url']
    return filedict


def save_uploads(uploads: dict, fp: Path='./uploads.json'):
    """
    """
    L = getLogger(__name__)
    l = len(uploads)
    if fp.parent.exists():
        with open(fp, 'w') as f:
            json.dump(uploads, fp=f, indent=2)
        L.info(f'Wrote {l} uploads to {fp}')
        L.debug(f'Saved upload dump:\n{json.dumps(uploads,indent=2)}')
        return fp
    else:
        L.error(f'Could not find folder to write uploads file! Dumping them here:\n{json.dumps(uploads, indent=2)}')


def load_uploads(fp: Path='./uploads.json'):
    """
    """
    L = getLogger(__name__)
    if fp.exists():
        L.info(f'Loading uploads from {fp}')
        with open(fp, 'r') as f:
            try:
                uploads = json.load(fp=f)
            except json.JSONDecodeError as e:
                L.warning(f'Caught JSONDecodeError: {e}. This probably happened because there is no file to read. Continuing with empty dict...')
                uploads = {}
        l = len(uploads)
        L.info(f'Loaded info for {l} uploads.')
        L.debug(f'Loaded upload dump:\n{json.dumps(uploads,indent=2)}')
        return uploads
    else:
        L.error('Could not find uploads file!')
        raise FileNotFoundError('Could not find an uploads info json file!')
