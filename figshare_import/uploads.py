import json
from pathlib import Path
from logging import getLogger

def save_uploads(uploads: dict, fp: Path='./uploads.json'):
    """
    """
    L = getLogger(__name__)
    l = len(uploads)
    if fp.parent.exists():
        if fp.exists():
            json.dump(uploads, fp=fp, indent=2)
        else:
            json.dump(uploads, fp=fp, indent=2)
        L.info(f'Wrote {l} uploads to {fp}')
        return fp
    else:
        L.error(f'Could not find folder to write uploads file! Dumping them here:\n{json.dumps(uploads, indent=2)}')

def load_uploads(fp: Path='./uploads.json'):
    """
    """
    L = getLogger(__name__)
    if fp.exists():
        L.info(f'Loading uploads from {fp}')
        uploads = json.load(fp=fp)
        l = len(uploads)
        L.info(f'Loaded info for {l} uploads.')
        return uploads
    else:
        L.error('Could not find uploads file!')
        raise FileNotFoundError('Could not find an uploads info json file!')
