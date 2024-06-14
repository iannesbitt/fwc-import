import json
from pathlib import Path
from logging import getLogger

def save_uploads(uploads: dict, fp: Path='./uploads.json'):
    """
    """
    L = getLogger(__name__)
    l = len(uploads)
    if fp.parent.exists():
        with open(fp, 'w') as f:
            json.dump(uploads, fp=f, indent=2)
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
        with open(fp, 'r') as f:
            try:
                uploads = json.load(fp=f)
            except json.JSONDecodeError as e:
                L.warning(f'Caught JSONDecodeError: {e}. This probably happened because there is no file to read. Continuing with empty dict...')
                uploads = {}
        l = len(uploads)
        L.info(f'Loaded info for {l} uploads.')
        return uploads
    else:
        L.error('Could not find uploads file!')
        raise FileNotFoundError('Could not find an uploads info json file!')
