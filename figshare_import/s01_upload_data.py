import uuid
import hashlib
import datetime
from pathlib import Path
import json

from d1_client.mnclient_2_0 import *
from d1_common.types import dataoneTypes
from d1_common.resource_map import createSimpleResourceMap

from logging import getLogger
from logging.config import dictConfig
CONFIG_LOC = Path('~/.config/figshare-import/').expanduser().absolute()
LOGCONFIG = CONFIG_LOC.joinpath('log/config.json')
with open(LOGCONFIG, 'r') as lc:
    LOGGING_CONFIG = json.load(lc)
dictConfig(LOGGING_CONFIG)
WORK_LOC = Path('~/figshare-import/').expanduser().absolute()

global DATA_ROOT
DATA_ROOT = Path('')

from .defs import fmts
from .uploads import load_uploads, save_uploads
from .utils import parse_name
# try:
#     from .defs import fmts
# except:
#     fmts = {'.xls': 'application/vnd.ms-excel','.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','.doc': 'application/msword','.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document','.ppt': 'application/vnd.ms-powerpoint','.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation','.pdf': 'application/pdf','.txt': 'text/plain','.zip': 'application/zip','.ttl': 'text/turtle','.md': 'text/markdown','.rmd': 'text/x-rmarkdown','.csv': 'text/csv','.bmp': 'image/bmp','.gif': 'image/gif','.jpg': 'image/jpeg','.jpeg': 'image/jpeg','.jp2': 'image/jp2','.png': 'image/png','.tif': 'image/geotiff','.svg': 'image/svg+xml','.nc': 'netCDF-4','.py': 'application/x-python','.hdf': 'application/x-hdf','.hdf5': 'application/x-hdf5','.tab': 'text/plain','.gz': 'application/x-gzip','.html': 'text/html','.htm': 'text/html','.xml': 'text/xml','.ps': 'application/postscript','.tsv': 'text/tsv','.rtf': 'application/rtf','.mp4': 'video/mp4','.r': 'application/R','.rar': 'application/x-rar-compressed','.fasta': 'application/x-fasta','.fastq': 'application/x-fasta','.fas': 'application/x-fasta','.gpx': 'application/gpx+xml'}

split_str = '<qdc:qualifieddc '
rpt_txt = """
Package creation report:
Failed uploads:     %s
Successful uploads: %s

Failed packages:
%s

Successful packages:
%s
"""

def get_token():
    """
    Paste your auth token into '~/.d1_token'
    """
    # Set the D1 token
    with open(Path(CONFIG_LOC / '.d1_token'), 'r') as tf:
        return tf.read().split('\n')[0]


def get_config():
    """
    Config values that are not the d1 token go in 'config.json'.
    """
    global DATA_ROOT
    # Set your ORCID
    CONFIG = CONFIG_LOC.joinpath('config.json')
    with open(CONFIG, 'r') as lc:
        config = json.load(lc)
    DATA_ROOT = Path(config['data_root'])
    return config['rightsholder_orcid'], config['nodeid'], config['mnurl'], str(Path(config['metadata_json']).expanduser())


def generate_sys_meta(pid: str, sid: str, format_id: str, size: int, md5, now, orcid: str):
    """
    Fills out the system metadata object with the needed properties
    :param pid: The pid of the system metadata document
    :param format_id: The format of the document being described
    :param size: The size of the document that is being described
    :param md5: The md5 hash of the document being described
    :param now: The current time
    :param orcid: The uploader's orcid
    """
    # create sysmeta and fill out relevant fields
    sys_meta = dataoneTypes.systemMetadata()
    sys_meta.identifier = str(pid)
    #sys_meta.seriesId = sid
    sys_meta.formatId = format_id
    sys_meta.size = size
    sys_meta.rightsHolder = orcid
    # calculate checksums, set dates, and set public access
    sys_meta.checksum = dataoneTypes.checksum(str(md5))
    sys_meta.checksum.algorithm = 'MD5'
    sys_meta.dateUploaded = now
    sys_meta.dateSysMetadataModified = now
    sys_meta.accessPolicy = generate_public_access_policy()
    return sys_meta


def generate_system_metadata(pid: str, sid: str, format_id: str, science_object: bytes, orcid: str):
    """
    Generates a system metadata document.
    :param pid: The pid that the object will have
    :param format_id: The format of the object (e.g text/csv)
    :param science_object: The object that is being described
    :return:
    """
    L = getLogger(__name__)
    # Check that the science_object is unicode, attempt to convert it if it's a str
    if not isinstance(science_object, bytes):
        if isinstance(science_object, str):
            science_object = science_object.encode("utf-8")
        else:
            raise ValueError('Supplied science_object is not unicode')
    size = len(science_object)
    L.debug(f'Object is {size} bytes ({round(size/(1024*1024), 1)} MB)')
    md5 = hashlib.md5()
    md5.update(science_object)
    md5 = md5.hexdigest()
    now = datetime.datetime.now()
    sys_meta = generate_sys_meta(pid, sid, format_id, size, md5, now, orcid)
    return sys_meta, md5, size


def generate_public_access_policy():
    """
    Creates the access policy for the object. Note that the permission is set to 'read'.
    """
    accessPolicy = dataoneTypes.accessPolicy()
    accessRule = dataoneTypes.AccessRule()
    accessRule.subject.append(d1_common.const.SUBJECT_PUBLIC)
    permission = dataoneTypes.Permission('read')
    accessRule.permission.append(permission)
    accessPolicy.append(accessRule)
    return accessPolicy


def get_format(fmt: Path):
    """
    Test the format based on the file suffix. If none is found, fall back to
    application/octet-stream.
    """
    L = getLogger(__name__)
    if fmt.suffix:
        format_id = fmts.get(fmt.suffix.lower())
        if format_id:
            L.debug(f'Found format id {format_id}')
            return format_id
    L.debug(f'No format id could be found. Using "application/octet-stream"')
    return "application/octet-stream"


def search_versions(doi: str):
    """
    Search the directory structure for a given DOI. If no dir is found, then
    decrease the version at the end of the DOI until a directory is found that
    matches. Return a list of files.
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


def get_filepaths(files: list, doidir: Path):
    """
    """
    paths = []
    for f in files:
        p = Path(doidir / f['name'])
        if p.exists():
            paths.append(p)
        else:
            for pa in Path(p.parent / p.stem).glob('*'):
                paths.append(pa)
    return paths


def upload_files(orcid: str, doi: str, files: list, client: MemberNodeClient_2_0):
    """
    """
    L = getLogger(__name__)
    data_pids = None
    sm_dict = {}
    # Create and upload the EML
    # Get and upload the data
    doidir = Path(DATA_ROOT / doi)
    if not doidir.exists():
        L.info(f'{doidir} does not exist. Trying other versions...')
        doidir = search_versions(doi)
    files = get_filepaths(doidir=doidir, files=files)
    flen = len(files)
    if flen == 0:
        raise FileNotFoundError(f'{doi} No files found for this version chain!')
    # keep track of data pids for resource mapping
    data_pids = []
    i = 0
    for f in files:
        i += 1
        try:
            fformat = get_format(f)
            data_pid = f"urn:uuid:{str(uuid.uuid4())}"
            L.debug(f'{doi} Reading {f.name}')
            data_bytes = f.read_bytes()
            L.debug(f'{doi} Generating sysmeta for {f.name}')
            data_sm, md5, size = generate_system_metadata(pid=data_pid,
                                                        sid=doi,
                                                        format_id=fformat,
                                                        science_object=data_bytes,
                                                        orcid=orcid)
            L.info(f'{doi} ({i}/{flen}) Uploading {f.name} ({round(size/(1024*1024), 1)} MB)')
            dmd = client.create(data_pid, data_bytes, data_sm)
            L.debug(f'{doi} Received response for science object upload:\n{dmd}')
            data_pids.append(data_pid)
            sm_dict[md5] = {'filename': f.name, 'size': size, 'doi': doi}
        except Exception as e:
            L.error(f'{doi} upload failed ({e})')
            raise BaseException(e)
    return sm_dict


def report(succ: int, fail: int, finished_dois: list, failed_dois: list):
    """
    Generate a short report with the successes and failures of the process.
    """
    L = getLogger(__name__)
    finished_str = "\n".join(str(x) for x in finished_dois)
    failed_str = "\n".join(str(x) for x in failed_dois)
    L.info(rpt_txt % (fail, succ, failed_str, finished_str))


def upload_manager(articles: list, orcid: str, client: MemberNodeClient_2_0, node: str):
    """
    Package creation and upload loop.
    """
    L = getLogger(__name__)
    n = len(articles)
    i = 0
    er = 0
    succ_list = []
    err_list = []
    uploads_loc = Path(WORK_LOC / f'{node}.json')
    try:
        uploads = load_uploads(uploads_loc)
    except FileNotFoundError:
        uploads = {}
    try:
        for article in articles:
            i += 1
            L.debug(f'Article:\n{article}')
            doi = article.get('doi')
            L.info(f'({i}/{n}) Working on {doi}')
            files = article.get('files')
            if not (uploads.get(doi)):
                uploads[doi] = {}
            else:
                prev_upls = 0
                for uf in uploads.get(doi):
                    L.debug(f'uploaded file: {uploads[doi][uf]}')
                    fn = 0
                    for f in files:
                        L.debug(f'known file: {files[fn]}')
                        if uploads[doi][uf]['filename'] == f['name']:
                            prev_upls += 1
                            del files[fn]
                        fn += 1
                L.info(f'Found {prev_upls} files that were already uploaded associated with {doi}')
            try:
                if len(files) > 0:
                    sm_dict = upload_files(orcid, doi, files, client)
                    L.info(f'{doi} done. Uploaded {len(sm_dict)} files.')
                    for fi in sm_dict:
                        uploads[doi][fi] = sm_dict[fi]
                    save_uploads(uploads, fp=uploads_loc)
                else:
                    L.info(f'No files to upload for {doi}')
                succ_list.append(doi)
            except Exception as e:
                er += 1
                err_list.append(doi)
                L.error(f'{doi} / {repr(e)}: {e}')
    except KeyboardInterrupt:
        L.info('Caught KeyboardInterrupt; generating report...')
    finally:
        save_uploads(uploads, fp=uploads_loc)
        report(succ=i-er, fail=er, finished_dois=succ_list, failed_dois=err_list)


def get_articles(metadata_json):
    """
    """
    with open(metadata_json, 'r') as f:
        return json.load(fp=f)['articles']


def main():
    """
    Set config items then start upload loop.
    """
    L = getLogger(__name__)
    # Set config items
    auth_token = get_token()
    orcid, node, mn_url, metadata_json = get_config()
    L.info(f'Rightsholder ORCiD {orcid}')
    L.info(f'Using {node} at {mn_url}')
    L.info(f'Root path: {DATA_ROOT}')
    # Set the token in the request header
    options: dict = {
        "headers": {"Authorization": "Bearer " + auth_token},
        "timeout_sec": 9999,
        }
    # Create the Member Node Client
    client: MemberNodeClient_2_0 = MemberNodeClient_2_0(mn_url, **options)
    articles = get_articles(metadata_json)
    L.info(f'Found {len(articles)} metadata records')
    upload_manager(articles=articles, orcid=orcid, client=client, node=node)
    client._session.close()


if __name__ == "__main__":
    """
    Running directly
    """
    main()
