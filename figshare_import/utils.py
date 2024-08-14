import json
import re
from pygeodesy.namedTuples import LatLon3Tuple
from logging import getLogger
from d1_client.mnclient_2_0 import MemberNodeClient_2_0

from pathlib import Path
from logging import getLogger
from datetime import datetime

from .defs import GROUP_ID, CN_URL, CONFIG_LOC, CONFIG


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


def fix_datetime(date: str):
    """
    Fix the datetime string.

    :param date: The date string, formatted as '%Y-%m-%dT%H:%M:%SZ'.
    :type date: str
    :return: The fixed date string in '%Y-%m-%d' format.
    :rtype: str
    """
    return datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')


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
    L = getLogger(__name__)
    patterns = [
        r'\b([+-]?\d+(\.\d+)?)°?\s*,\s*([+-]?\d+(\.\d+)?)°?\b',  # 8.994410°, - 79.543000°
        r'\b([+-]?\d+(\.\d+)?)°?\s*([NS]),\s*([+-]?\d+(\.\d+)?)°?\s*([EW])\b',  # 8.910718°N, -79.528919°
        r'\b(\d+)°\s*(\d+(\.\d+)?)\'?\s*([NS]),\s*(\d+)°\s*(\d+(\.\d+)?)\'?\s*([EW])\b',  # 7° 38.422'N, 81° 42.079'W
        r'\b(\d+)°\s*(\d+)\'\s*(\d+(\.\d+)?)\"?\s*([NS]),\s*(\d+)°\s*(\d+)\'\s*(\d+(\.\d+)?)\"?\s*([EW])\b',  # 9°9'42.36"N, 79°50'15.67"W
        r'\b(\d+)°\s*(\d+)′\s*([NS])\s*latitude,\s*(\d+)°\s*(\d+)′\s*([EW])\s*longitude\b',  # 9°41′ S latitude, 76°24′ W longitude
        r'\b(\d+)°\s*(\d+(\.\d+)?)\'?\s*([NS])\s+(\d+)°\s*(\d+(\.\d+)?)\'?\s*([EW])\b'  # 8° 38.743'N    79° 2.887'W
    ]

    latlon = []

    if '°' in desc:
        for pattern in patterns:
            matches = re.findall(pattern, desc)
            for match in matches:
                L.info(f'Match list: {match}')
                if len(match) == 4:
                    # Decimal degrees format
                    lat = float(match[0])
                    lon = float(match[2])
                    L.info(f'Found decimal degrees; lat, lon: {lat}, {lon}')
                    latlon.append(LatLon3Tuple(lat, lon, 0))
                elif len(match) == 6:
                    # Decimal degrees with direction
                    lat = float(match[0]) * (-1 if match[2] == 'S' else 1)
                    lon = float(match[3]) * (-1 if match[5] == 'W' else 1)
                    L.info(f'Found directional decimal degrees; lat, lon: {lat}, {lon}')
                    latlon.append(LatLon3Tuple(lat, lon, 0))
                elif len(match) == 8:
                    # Degrees and decimal minutes with direction
                    lat = dms_to_decimal(match[0], match[1], 0, match[3])
                    lon = dms_to_decimal(match[4], match[5], 0, match[7])
                    L.info(f'Found DDM; lat, lon: {lat}, {lon}')
                    latlon.append(LatLon3Tuple(lat, lon, 0))
                elif len(match) == 10:
                    # Degrees, minutes, and seconds with direction
                    lat = dms_to_decimal(match[0], match[1], match[2], match[4])
                    lon = dms_to_decimal(match[5], match[6], match[7], match[9])
                    L.info(f'Found DMS; lat, lon: {lat}, {lon}')
                    latlon.append(LatLon3Tuple(lat, lon, 0))
        return latlon
    else:
        L.info('No lat/lon pairs found in description.')
        return None

def pathify(title: str):
    """
    Convert a title to a file path.

    :param title: The title to convert.
    :type title: str
    :return: The pathified title.
    :rtype: str
    """
    return re.sub(r'[^\w\s]', '', title).replace(' ', '_')[:48]


def get_doipath(doi: str):
    """
    Get the path to the data directory for a given DOI.

    :param doi: The DOI to search for.
    :type doi: str
    :return: The path to the data directory.
    :rtype: Path
    """
    L = getLogger(__name__)
    global DATA_ROOT
    doidir = Path(DATA_ROOT / doi)
    if not doidir.exists():
        L.info(f'{doidir} does not exist. Trying other versions...')
        doidir = search_versions(doi)
    return doidir


def search_versions(doi: str):
    """
    Search the directory structure for a given DOI. If no dir is found, then
    decrease the version at the end of the DOI until a directory is found that
    matches. Return a list of files.

    :param str doi: The DOI to search for.
    :return: The path to the data directory.
    :rtype: Path
    """
    global DATA_ROOT
    L = getLogger(__name__)
    doidir = Path(DATA_ROOT / doi)
    if not doidir.exists():
        # we need to figure out where the closest version is (or if it exists?)
        try:
            [doiroot, version] = doidir.__str__().split('.v')
            version = int(version)
            versions = 0
            L.info(f'{doi} starting with version {version}')
            while True:
                version -= 1
                moddir = Path(DATA_ROOT / f'{doiroot}.v{version}')
                L.info(f'Trying {moddir}')
                if moddir.exists():
                    return moddir
                else:
                    if version > 0:
                        continue
                    else:
                        L.info(f'Found {versions} versions of doi root {doi}')
                        break
        except ValueError:
            L.info(f'{doi} has no version.')
        except Exception as e:
            L.error(f'{repr(e)} has occurred: {e}')
    return doidir


def write_article(article: dict | str, doi: str, title: str, fmt: str):
    """
    Writes the article dictionary to a file.

    :param article: The article data to write.
    :type article: dict
    :param path: The format to write the article in (e.g., 'json', 'xml').
    :type path: Path
    """
    L = getLogger(__name__)
    doipath = get_doipath(doi)
    path = Path(doipath / f"{pathify(title)}.{fmt}")
    L.info(f'Writing {fmt} file to {path}')
    with open(str(Path(path)), 'w') as f:
        if fmt == 'json':
            json.dump(article, fp=f, indent=2)
        elif fmt == 'xml':
            f.write(article)
    L.info(f'Wrote {fmt}.')
    return path


def get_article_list(article_file: Path | str):
    """
    Retrieves the list of articles from the provided data.

    :param articles: The file containing article metadata.
    :type articles: dict or list
    :return: The list of articles.
    :rtype: list
    """
    L = getLogger(__name__)
    af = Path(article_file)
    articles = json.loads(af.read_bytes())
    alist = None
    try:
        alist = articles.get('articles')
    except:
        L.info(f'articles object is not a dict but {type(articles)}. Trying to use it as a list...')
    if alist:
        articles = alist
    else:
        if (type(articles) == list) and (len(articles) >= 1):
            L.info(f'articles object is a list of length {len(articles)}')
    L.info(f'Found {len(articles)} article records')
    return articles


def rectify_uploads(uploads: Path | str, client: MemberNodeClient_2_0 | None=None):
    """
    Rectify the uploads dictionary with the DataONE object identifiers.
    Write the updated uploads dictionary to the original file.

    :param Path uploads: A dictionary containing upload information.
    :param MemberNodeClient_2_0 client: A DataONE MemberNodeClient_2_0 object.
    :return: A dictionary with updated upload information.
    :rtype: dict
    """
    if type(uploads) == str:
        uploads = Path(uploads)
    if not uploads.exists():
        raise FileNotFoundError(f'Could not find an uploads info json file at {uploads}')
    if not client:
        orcid, node, mn_url, metadata_json = get_config()
        options: dict = {
            "headers": {"Authorization": "Bearer " + get_token()},
            "timeout_sec": 9999,
            }
        client = MemberNodeClient_2_0(mn_url, **options)
    uploads_dict = load_uploads(uploads)
    uploads_dict = get_d1_ids(uploads_dict, client)
    save_uploads(uploads_dict, fp=uploads)
    return uploads_dict


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
