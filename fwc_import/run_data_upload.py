import uuid
import hashlib
import datetime
from pathlib import Path

from d1_client.mnclient_2_0 import *
from d1_common.types import dataoneTypes, exceptions
from d1_common.resource_map import createSimpleResourceMap
from d1_common.resource_map import ResourceMap

from logging import getLogger
from copy import deepcopy

from .defs import fmts, CN_URL, DATA_ROOT, WORK_LOC
from .utils import load_uploads, save_uploads, \
            get_token, get_config, create_client, \
            generate_access_policy

rpt_txt = """
Package creation report:
Failed uploads:     %s
Successful uploads: %s

Failed packages:
%s

Successful packages:
%s
"""
"""
The package creation report text template.
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
    sys_meta.accessPolicy = generate_access_policy()
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


def sysmeta_obsolete_updates(client: MemberNodeClient_2_0, old_pid: str, new_pid: str):
    """
    Update the system metadata of the old object to include the obsoletedBy field.

    :param client: The Member Node client.
    :type client: MemberNodeClient_2_0
    :param old_pid: The PID of the old object.
    :type old_pid: str
    :param new_pid: The PID of the new object.
    :type new_pid: str
    """
    L = getLogger(__name__)
    # Retrieve old sysmeta
    old_system_metadata = client.getSystemMetadata(old_pid)
    if not old_system_metadata:
        L.error(f'Failed to retrieve system metadata for old PID: {old_pid}')
        return None
    new_system_metadata = client.getSystemMetadata(new_pid)
    if not new_system_metadata:
        L.error(f'Failed to retrieve system metadata for new PID: {new_pid}')
        return None
    # Add obsoletedBy pid to old sysmeta
    old_system_metadata.obsoletedBy = new_pid
    new_system_metadata.obsoletes = old_pid
    try:
        # Update old sysmeta object
        client.updateSystemMetadata(old_pid, old_system_metadata)
        L.info(f'Successfully updated system metadata for old PID: {old_pid} with obsoletedBy: {new_pid}')
    except Exception as e:
        L.error(f'Failed to update system metadata for old PID: {old_pid}: {repr(e)}')
        return None
    try:
        # Update new sysmeta object
        client.updateSystemMetadata(new_pid, new_system_metadata)
        L.info(f'Successfully updated system metadata for new PID: {new_pid} with obsoletes: {old_pid}')
    except Exception as e:
        L.error(f'Failed to update system metadata for new PID: {new_pid}: {repr(e)}')
        return None


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


def generate_resource_map(eml_pid: str, data_pids: list):
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
        ore_pid=f"resource_map_urn:uuid:{str(uuid.uuid4())}",
        scimeta_pid=eml_pid,
        sciobj_pid_list=data_pids,
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
                                                                                    format_id="http://www.openarchives.org/ore/terms",
                                                                                    science_object=resource_map_bytes,
                                                                                    orcid=orcid)
    resource_map_dmd = client.create(resource_map_pid, resource_map_bytes, resource_map_sm)
    if isinstance(resource_map_dmd, dataoneTypes.Identifier):
        try:
            L.info(f'{doi} Received response for resource map upload: {resource_map_dmd.value()}')
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
    Generate and print a short report with the successes and failures of the
    process.

    :param int succ: The number of successful uploads.
    :param int fail: The number of failed uploads.
    :param list finished_dois: The DOIs that were successfully uploaded.
    :param list failed_dois: The DOIs that failed to upload.
    """
    L = getLogger(__name__)
    finished_str = "\n".join(str(x) for x in finished_dois)
    failed_str = "\n".join(str(x) for x in failed_dois)
    L.info(rpt_txt % (fail, succ, failed_str, finished_str))


def upload_metadata_to_new_packages(eml_folder: str, orcid: str, client: MemberNodeClient_2_0, node: str):
    """
    Upload only metadata (EML) and data packages (resource maps) for each EML file in the given folder, using packageId as the identifier.

    :param eml_folder: Path to the folder containing EML files.
    :param orcid: The ORCID of the uploader.
    :param client: The Member Node client.
    :param node: The node identifier.
    """
    import xml.etree.ElementTree as ET
    L = getLogger(__name__)
    sep = '' if CN_URL.endswith('/') else '/'
    eml_dir = Path(eml_folder)
    eml_files = sorted(list(eml_dir.glob('*.xml')))
    n = len(eml_files)
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
        for eml_path in eml_files:
            old_eml_pid, old_resource_map_pid = None, None
            i += 1
            try:
                eml_string = eml_path.read_text(encoding='utf-8')
                # Parse packageId from EML header
                root = ET.fromstring(eml_string)
                package_id = root.attrib.get('packageId')
                if not package_id:
                    L.error(f'No packageId found in {eml_path.name}, skipping.')
                    er += 1
                    err_list.append(eml_path.name)
                    continue
                L.info(f'({i}/{n}) Working on {package_id} from {eml_path.name}')
                # Use packageId as the identifier
                if uploads.get(package_id) and uploads[package_id].get('eml'):
                    old_eml_pid = uploads[package_id]['eml']['identifier']
                    L.info(f'{package_id} Found previous EML: {old_eml_pid}')
                else:
                    if not uploads.get(package_id):
                        uploads[package_id] = {}
                eml_pid, eml_md5, eml_size = upload_eml(orcid, package_id, eml_string, client)
                if old_eml_pid:
                    L.info(f'{package_id} Adding obsoletedBy to old EML sysmeta object: {old_eml_pid}')
                    sysmeta_obsolete_updates(client, old_eml_pid, eml_pid)
                if eml_pid:
                    uploads[package_id]['eml'] = {
                        'filename': eml_path.name,
                        'size': eml_size,
                        'doi': package_id,
                        'identifier': eml_pid,
                        'md5': eml_md5,
                        'formatId': "https://eml.ecoinformatics.org/eml-2.2.0",
                        'url': f"{CN_URL}{sep}v2/resolve/{eml_pid}",
                    }
                    save_uploads(uploads, fp=uploads_loc)
                    # Generate the DataONE resource map (with only the EML PID)
                    pid_list = [eml_pid]
                    resource_map = generate_resource_map(eml_pid=eml_pid, data_pids=pid_list)
                    if uploads[package_id].get('resource_map'):
                        old_resource_map_pid = uploads[package_id]['resource_map']['identifier']
                        L.info(f'{package_id} Found previous resource map: {old_resource_map_pid}')
                    resource_map_pid, resource_map_md5, resource_map_size = upload_resource_map(
                        doi=package_id,
                        resource_map=resource_map,
                        client=client,
                        orcid=orcid,
                    )
                    if old_resource_map_pid:
                        L.info(f'{package_id} Adding obsoletedBy to old resource map sysmeta object: {old_resource_map_pid}')
                        sysmeta_obsolete_updates(client, old_pid=old_resource_map_pid, new_pid=resource_map.getResourceMapPid())
                    if resource_map_pid:
                        uploads[package_id]['resource_map'] = {
                            'filename': 'resource_map.xml',
                            'size': resource_map_size,
                            'doi': package_id,
                            'identifier': resource_map_pid,
                            'md5': resource_map_md5,
                            'formatId': "http://www.openarchives.org/ore/terms",
                            'url': f"{CN_URL}{sep}v2/resolve/{resource_map_pid}",
                        }
                        save_uploads(uploads, fp=uploads_loc)
                        L.info(f'{package_id} Resource map uploaded successfully: {resource_map_pid}')
                    else:
                        uploads[package_id]['resource_map'] = None
                        raise exceptions.DataONEException(f'{package_id} Resource map upload failed')
                else:
                    uploads[package_id]['eml'] = None
                    raise exceptions.DataONEException(f'{package_id} EML upload failed')
                succ_list.append(package_id)
            except Exception as e:
                er += 1
                err_list.append(str(eml_path))
                L.error(f'{eml_path} / {repr(e)}')
    except KeyboardInterrupt:
        L.info('Caught KeyboardInterrupt; generating report...')
    finally:
        save_uploads(uploads, fp=uploads_loc)
        report(succ=i-er, fail=er, finished_dois=succ_list, failed_dois=err_list)

def run_data_upload():
    """
    Set config items then start upload loop. This function is called when the
    script is run directly.
    """
    L = getLogger(__name__)
    # Set config items
    auth_token = get_token()
    config = get_config()
    orcid = config.get('rightsholder_orcid')
    node = config.get('nodeid')
    mn_url = config.get('mnurl')
    data_root = config.get('data_root', 'output_eml')
    L.info(f'Rightsholder ORCiD {orcid}')
    L.info(f'Using {node} at {mn_url}')
    L.info(f'Metadata path: {DATA_ROOT}')
    # Create the Member Node Client
    client: MemberNodeClient_2_0 = create_client(mn_url, auth_token=auth_token)
    L.info(f'Uploading EMLs from folder: {data_root}')
    upload_metadata_to_new_packages(eml_folder=data_root, orcid=orcid, client=client, node=node)
    client._session.close()


if __name__ == "__main__":
    """
    Running directly.
    """
    run_data_upload()
