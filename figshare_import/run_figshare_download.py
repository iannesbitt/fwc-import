import json
from pathlib import Path
import requests
from tqdm import tqdm
import hashlib

from .utils import get_config

def get_articles(config):
    """
    Get DOIs from article details

    :return: json contents of article details
    :rtype: json
    """
    with open(Path(config['metadata_json']), 'r') as f:
        return json.load(f)


def get_dois(contents: json):
    """
    Get DOIs from a list of articles

    :param json contents: json contents of article details
    :return: list of dois, set of shoulders
    :rtype: list, set
    """
    dois = []
    shoulders = set()
    for a in contents.get('articles'):
        doi = a.get('doi')
        dois.append(doi)
        shoulders.add(doi.split('/')[0])
    return dois, shoulders


def make_dirs(dois: list, config: dict):
    """
    Make directories pertaining to each DOI

    :param list dois: list of dois
    """
    cur = Path(config['data_root'])
    for doi in dois:
        Path(cur / doi).mkdir(exist_ok=True, parents=True)


def get_files(contents: json):
    """
    Get a dict of files to download from figshare

    :param json contents: json contents of article details
    :return: dict of files to download
    """
    files = {}
    for a in contents.get('articles'):
        doi = a.get('doi')
        if not doi:
            print('no doi')
        flist = a.get('files')
        for f in flist:
            cmd5 = f.get('computed_md5')
            smd5 = f.get('supplied_md5')
            if cmd5 != smd5:
                print(f'md5sums do not match for doi:{doi}\nsupplied: {smd5}\ncomputed: {cmd5}')
            if not cmd5:
                cmd5 = smd5
            files[f.get('download_url')] = [doi, f.get('name'), f.get('size'), cmd5]
    return files


def dl_f(session: requests.Session, url: str, path: Path, fnum: str, write_mode: str):
    """
    Download a file

    :param requests.Session session: requests session
    :param str url: url to download
    :param Path path: path to save file
    :param str fnum: file number
    :param str write_mode: write mode
    :return: size of file
    :rtype: int
    """
    r = session.get(url=url, stream=True)
    total = int(r.headers.get('content-length', 0))
    with open(path, write_mode) as file, tqdm(
            desc=f'{fnum}: {path}',
            total=total,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
        for data in r.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)
    return path.stat().st_size


def check_hash(file):
    """
    Calculate the md5 of a file

    :param str file: path to file
    :return: md5 hash of file
    :rtype: str
    """
    return hashlib.md5(open(file,'rb').read()).hexdigest()


def dl_files(files: dict, config: dict):
    """
    Download files

    :param dict files: dict of files to download
    """
    data_root = Path(config['data_root'])
    fc = len(files)
    fn = 0
    with requests.Session() as session:
        for f in files:
            fn += 1
            url = f
            path = Path(f'{data_root}/{files[f][0]}/{files[f][1]}')
            size = files[f][2]
            md5f = files[f][3]
            wm = 'wb'
            prev_hash = None
            prev_size = None
            fnum = f'({fn}/{fc})'
            if path.exists():
                if md5f == check_hash(path):
                    print(f'{fnum}: hash match.')
                    continue
                else:
                    path.unlink()
            while True:
                try:
                    s = dl_f(session=session, url=url, path=path, fnum=fnum, write_mode=wm)
                    if s == size:
                        sum = check_hash(file=path)
                        if sum == md5f:
                            print('Hash match.')
                            break
                        else:
                            print(f'Downloaded md5 does not match reported: {fn} / {url}\n'
                                  f'Calculated: {sum}\n'
                                  f'Reported: {md5f}')
                            if not prev_hash:
                                prev_hash = sum
                            else:
                                if md5f == prev_hash:
                                    print('Previous two hashes match, but do not match the reported hash; continuing with next file...')
                                    break
                                else:
                                    prev_hash = sum
                    else:
                        print(f'Size inconsistency with {fn} / {url}')
                        print(f'Reported filesize: {size}\n'
                              f'Download filesize: {s}')
                        if not prev_size:
                            prev_size = s
                        else:
                            if s == prev_size:
                                print('Previous two sizes match, but do not match the reported size; continuing with next file...')
                                break
                            else:
                                prev_size = s
                        path.unlink()
                    print('Overwriting previous bytes due to download failure')
                    wm = 'w+b'
                except KeyboardInterrupt as e:
                    print(f'Process interrupted.')
                    exit(1)
                except Exception as e:
                    print(f'Error with {url}')
                    print(f"{repr(e)}: {e}")


def run_figshare_download():
    """
    Run the script
    """
    config = get_config()
    jc = get_articles(config)
    dois, shoulders = get_dois(jc)
    make_dirs(dois, config)
    files = get_files(jc)
    print(f'Attempting to download {len(files)} files...')
    dl_files(files, config)


if __name__ == "__main__":
    """
    Running from the command line
    """
    run_figshare_download()
