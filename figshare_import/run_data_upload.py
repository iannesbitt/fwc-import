import uuid
import hashlib
import datetime
from pathlib import Path

from d1_client.mnclient_2_0 import *
from d1_common.types import dataoneTypes
from d1_common.resource_map import createSimpleResourceMap
from d1_common.resource_map import ResourceMap

from logging import getLogger

from .defs import fmts, CN_URL, DATA_ROOT, WORK_LOC
from .utils import get_article_list, load_uploads, save_uploads, write_article, get_token, get_config, get_doipath
from .conv import figshare_to_eml

rpt_txt = """
Package creation report:
Failed uploads:     %s
Successful uploads: %s

Failed packages:
%s

Successful packages:
%s
"""


def generate_sys_meta(pid: str, sid: str, format_id: str, size: int, md5, now, orcid: str):
    """
    Fills out the system metadata object with the needed properties

    :param pid: The pid of the system metadata document
    :param format_id: The format of the document being described
    :param size: The size of the document that is being described
    :param md5: The md5 hash of the document being described
    :param now: The current time
    :param orcid: The uploader's orcid
    :return: The system metadata document
    :rtype: dataoneTypes.systemMetadata
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
    :return: The system metadata document, MD5 sum, and size of the object
    :rtype: tuple
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
    
    :return: The access policy.
    :rtype: dataoneTypes.accessPolicy
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

    :param Path fmt: The file to test.
    :return: The format id.
    :rtype: str
    """
    L = getLogger(__name__)
    if fmt.suffix:
        format_id = fmts.get(fmt.suffix.lower())
        if format_id:
            L.debug(f'Found format id {format_id}')
            return format_id
    L.debug(f'No format id could be found. Using "application/octet-stream"')
    return "application/octet-stream"


def get_filepaths(files: list, doidir: Path):
    """
    Get the paths to the files in the data directory.

    :param list files: The list of files to search for.
    :param Path doidir: The path to the data directory.
    :return: The list of paths to the files.
    :rtype: list
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


def upload_files(orcid: str, doi: str, files: list[Path], client: MemberNodeClient_2_0):
    """
    Upload the files to the Member Node.

    :param str orcid: The ORCID of the uploader.
    :param str doi: The DOI of the article.
    :param list files: The list of files to upload.
    :param client: The Member Node client.
    :type client: MemberNodeClient_2_0
    :return: A dictionary of checksums and file information.
    :rtype: dict
    """
    L = getLogger(__name__)
    global CN_URL
    sep = '' if CN_URL.endswith('/') else '/'
    data_pids = None
    sm_dict = {}
    # Create and upload the EML
    # Get and upload the data
    doidir = get_doipath(doi)
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
            if isinstance(dmd, dataoneTypes.Identifier):
                try:
                    L.info(f'{doi} Received response for science object upload: {dmd.value()}\n{dmd}')
                except Exception as e:
                    L.error(f'{doi} Received <d1_common.types.generated.dataoneTypes_v1.Identifier> but could not print value: {repr(e)}')
                data_pids.append(data_pid)
                sm_dict[md5] = {
                    'filename': f.name,
                    'size': size,
                    'doi': doi,
                    'identifier': data_pid,
                    'formatId': fformat,
                    'url': f"{CN_URL}{sep}v2/resolve/{data_pid}",
                }
            else:
                L.error(f'{doi} Unexpected response type: {type(dmd)}')
                try:
                    L.debug(f'{doi} Received response:\n{dmd.value()}')
                except Exception as e:
                    L.error(f'{doi} Could not print response: {repr(e)}')
        except Exception as e:
            L.error(f'{doi} upload failed ({e})')
            raise BaseException(e)
    return sm_dict


def upload_eml(orcid: str, doi: str, eml: str, client: MemberNodeClient_2_0):
    """
    Upload the EML to the Member Node.
    
    :param str orcid: The ORCID of the uploader.
    :param str doi: The DOI of the article.
    :param str eml: The EML to upload.
    :param client: The Member Node client.
    :type client: MemberNodeClient_2_0
    :return: The identifier of the EML.
    :rtype: str
    """
    L = getLogger(__name__)
    eml_pid = f"urn:uuid:{str(uuid.uuid4())}"
    eml_bytes = eml.encode("utf-8")
    eml_sm, eml_md5, eml_size = generate_system_metadata(pid=eml_pid,
                                                         sid=doi,
                                                         format_id="https://eml.ecoinformatics.org/eml-2.2.0",
                                                         science_object=eml_bytes,
                                                         orcid=orcid)
    eml_dmd = client.create(eml_pid, eml_bytes, eml_sm)
    if isinstance(eml_dmd, dataoneTypes.Identifier):
        try:
            L.info(f'{doi} Received response for EML upload: {eml_dmd.value()}\n{eml_dmd}')
            if eml_dmd.value() == eml_pid:
                L.info(f'{doi} EML uploaded successfully: {eml_pid}')
            else:
                L.error(f'{doi} EML identifier does not match D1 identifier! {eml_pid} != {eml_dmd.value()}')
        except Exception as e:
            L.error(f'{doi} Received <d1_common.types.generated.dataoneTypes_v1.Identifier> but could not print value: {repr(e)}')
        return eml_pid, eml_md5, eml_size
    else:
        L.error(f'{doi} Unexpected response type: {type(eml_dmd)}')
        try:
            L.debug(f'{doi} Received response:\n{eml_dmd.value()}')
        except Exception as e:
            L.error(f'{doi} Could not print response: {repr(e)}')
        return None


def generate_resource_map(doi: str, eml_pid: str, data_pids: list):
    """
    Generate the resource map XML for the given DOI, EML PID, and data PIDs.

    :param str doi: The DOI of the article.
    :param str eml_pid: The PID of the EML.
    :param list data_pids: The list of data PIDs.
    :return: The resource map XML.
    :rtype: str
    """
    L = getLogger(__name__)
    resource_map: ResourceMap = createSimpleResourceMap(
        ore_pid=f"urn:uuid:{str(uuid.uuid4())}",
        scimeta_pid=eml_pid,
        scidata_pid_list=data_pids,
    )
    L.debug(f"Generated resource map:\n{resource_map}")
    return resource_map


def upload_resource_map(doi: str, resource_map: ResourceMap, client: MemberNodeClient_2_0, orcid: str):
    """
    Upload the resource map to the Member Node.

    :param str doi: The DOI of the article.
    :param resource_map: The resource map XML.
    :type resource_map: ResourceMap
    :param client: The Member Node client.
    :type client: MemberNodeClient_2_0
    :return: The identifier of the resource map.
    :rtype: str
    """
    L = getLogger(__name__)
    resource_map_pid = resource_map.getResourceMapPid()
    resource_map_bytes = resource_map.serialize(format="xml")
    resource_map_sm, resource_map_md5, resource_map_size = generate_system_metadata(pid=resource_map_pid,
                                                                                    sid=doi,
                                                                                    format_id="http://www.openarchives.org/ore/terms/ResourceMap",
                                                                                    science_object=resource_map_bytes,
                                                                                    orcid=orcid)
    resource_map_dmd = client.create(resource_map_pid, resource_map_bytes, resource_map_sm)
    if isinstance(resource_map_dmd, dataoneTypes.Identifier):
        try:
            L.info(f'{doi} Received response for resource map upload: {resource_map_dmd.value()}\n{resource_map_dmd}')
            if resource_map_dmd.value() == resource_map_pid:
                L.info(f'{doi} Resource map uploaded successfully: {resource_map_pid}')
            else:
                L.error(f'{doi} Resource map identifier does not match D1 identifier! {resource_map_pid} != {resource_map_dmd.value()}')
        except Exception as e:
            L.error(f'{doi} Received <d1_common.types.generated.dataoneTypes_v1.Identifier> but could not print value: {repr(e)}')
        return resource_map_pid, resource_map_md5, resource_map_size
    else:
        L.error(f'{doi} Unexpected response type: {type(resource_map_dmd)}')
        try:
            L.debug(f'{doi} Received response:\n{resource_map_dmd.value()}')
        except Exception as e:
            L.error(f'{doi} Could not print response: {repr(e)}')
        return None


def report(succ: int, fail: int, finished_dois: list, failed_dois: list):
    """
    Generate a short report with the successes and failures of the process.

    :param int succ: The number of successful uploads.
    :param int fail: The number of failed uploads.
    :param list finished_dois: The DOIs that were successfully uploaded.
    :param list failed_dois: The DOIs that failed to upload.
    """
    L = getLogger(__name__)
    finished_str = "\n".join(str(x) for x in finished_dois)
    failed_str = "\n".join(str(x) for x in failed_dois)
    L.info(rpt_txt % (fail, succ, failed_str, finished_str))


def upload_manager(articles: list, orcid: str, client: MemberNodeClient_2_0, node: str):
    """
    Package creation and upload loop. This function will create packages and
    upload them to the Member Node.

    :param list articles: The list of articles to upload.
    :param str orcid: The ORCID of the uploader.
    :param client: The Member Node client.
    :type client: MemberNodeClient_2_0
    :param str node: The node identifier.
    """
    L = getLogger(__name__)
    sep = '' if CN_URL.endswith('/') else '/'
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
            title = article.get('title')
            L.info(f'({i}/{n}) Working on {doi}')
            write_article(article=article, doi=doi, title=title, fmt='json')
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
                        for f in files:
                            if f['name'] == sm_dict[fi]['filename'] and f['computed_md5'] == sm_dict[fi]['md5']:
                                f['d1_url'] = sm_dict[fi]['url']
                    save_uploads(uploads, fp=uploads_loc)
                    # Convert the article to EML
                    eml_string = figshare_to_eml(article)
                    # Write the EML to file
                    write_article(article=article, doi=doi, title=title, fmt='xml')
                    # Upload the EML to the Member Node
                    eml_pid, eml_md5, eml_size = upload_eml(orcid, doi, eml_string, client)
                    if eml_pid:
                        uploads[doi]['eml'] = {
                            'filename': "eml_2_2_0.xml",
                            'size': eml_size,
                            'doi': doi,
                            'identifier': eml_pid,
                            'md5': eml_md5,
                            'formatId': "https://eml.ecoinformatics.org/eml-2.2.0",
                            'url': f"{CN_URL}{sep}v2/resolve/{eml_pid}",
                        }
                        save_uploads(uploads, fp=uploads_loc)
                        # Generate the DataONE resource map
                        pid_list = []
                        for file_info in files:
                            pid_list.append(file_info['identifier'])
                        pid_list.append(eml_pid)
                        resource_map = generate_resource_map(doi=doi, eml_pid=eml_pid, data_pids=pid_list)
                        # Upload the resource map to the Member Node
                        resource_map_pid, resource_map_md5, resource_map_size = upload_resource_map(orcid, doi, resource_map, client)
                        # Put the resource map info in the uploads dictionary
                        if resource_map_pid:
                            uploads[doi]['resource_map'] = {
                                'filename': 'resource_map.xml',
                                'size': resource_map_size,
                                'doi': doi,
                                'identifier': resource_map_pid,
                                'md5': resource_map_md5,
                                'formatId': "http://www.openarchives.org/ore/terms/ResourceMap",
                                'url': f"{CN_URL}{sep}v2/resolve/{resource_map_pid}",
                            }
                            save_uploads(uploads, fp=uploads_loc)
                            L.info(f'{doi} Resource map uploaded successfully: {resource_map_pid}')
                        else:
                            L.error(f'{doi} Resource map upload failed')
                    else:
                        L.error(f'{doi} EML upload failed')
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


def main():
    """
    Set config items then start upload loop. This function is called when the
    script is run directly.
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
    articles = get_article_list(metadata_json)
    L.info(f'Found {len(articles)} metadata records')
    upload_manager(articles=articles, orcid=orcid, client=client, node=node)
    client._session.close()


if __name__ == "__main__":
    """
    Running directly.
    """
    main()
