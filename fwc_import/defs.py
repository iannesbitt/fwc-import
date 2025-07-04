import json
from pathlib import Path
from logging import getLogger
from logging.config import dictConfig

global CN_URL
CN_URL = "https://cn-stage.test.dataone.org/cn"
"""
The URL for the Coordinating Node.
Defaults to the DataONE staging CN: ``https://cn-stage.test.dataone.org/cn``
"""

global DATA_ROOT
DATA_ROOT = Path('')
"""
The root directory for the data files.
Defaults to the current directory but should be set appropriately in the
config file.
"""

global CONFIG
CONFIG = {
    "rightsholder_orcid": "http://orcid.org/0000-0001-5828-6070",
    "write_groups": ["CN=Test_Group,DC=dataone,DC=org"],
    "changePermission_groups": ["CN=Test_Group,DC=dataone,DC=org"],
    "nodeid": "urn:node:mnTestKNB",
    "mnurl": "https://dev.nceas.ucsb.edu/knb/d1/mn/",
    "cnurl": "https://cn-stage.test.dataone.org/cn",
    "metadata_json": "~/fwc-import/article-details-test.json",
    "data_root": "/mnt/ceph/repos/fwc/fwc-import/"
}
"""
The configuration dictionary. These values are read from the config file.
Defaults to the values above but should be set appropriately in the config file.
"""

CONFIG_LOC = Path('~/.config/fwc-import/').expanduser().absolute()
"""
The location of the configuration file.
Defaults to ``~/.config/fwc-import/``.
"""

LOGCONFIG = CONFIG_LOC.joinpath('log/config.json')
"""
The location of the logging configuration file.
Defaults to ``~/.config/fwc-import/log/config.json``.
"""

with open(LOGCONFIG, 'r') as lc:
    LOGGING_CONFIG = json.load(lc)
    """
    The logging configuration dictionary.
    Defaults to the values in the file specified by ``LOGCONFIG``.
    """

dictConfig(LOGGING_CONFIG)
WORK_LOC = Path('~/fwc-import/').expanduser().absolute()
"""
The location of the working directory.
Defaults to ``~/fwc-import/``.
"""

# a list of formats and their 
fmts = {
    '.xls': 'application/vnd.ms-excel',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.ppt': 'application/vnd.ms-powerpoint',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.pdf': 'application/pdf',
    '.txt': 'text/plain',
    '.zip': 'application/zip',
    '.ttl': 'text/turtle',
    '.md': 'text/markdown',
    '.rmd': 'text/x-rmarkdown',
    '.csv': 'text/csv',
    '.bmp': 'image/bmp',
    '.gif': 'image/gif',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.jp2': 'image/jp2',
    '.png': 'image/png',
    '.tif': 'image/geotiff',
    '.tiff': 'image/geotiff',
    '.svg': 'image/svg+xml',
    '.nc': 'netCDF-4',
    '.py': 'application/x-python',
    '.hdf': 'application/x-hdf',
    '.hdf5': 'application/x-hdf5',
    '.tab': 'text/plain',
    '.gz': 'application/x-gzip',
    '.html': 'text/html',
    '.htm': 'text/html',
    '.xml': 'text/xml',
    '.ps': 'application/postscript',
    '.tsv': 'text/tsv',
    '.rtf': 'application/rtf',
    '.mp4': 'video/mp4',
    '.r': 'application/R',
    '.rar': 'application/x-rar-compressed',
    '.fasta': 'application/x-fasta',
    '.fastq': 'application/x-fasta',
    '.fas': 'application/x-fasta',
    '.gpx': 'application/gpx+xml',
    '.json': 'application/json',
    '.geojson': 'application/geo+json',
    '.shp': 'application/x-qgis',
}
"""
A dictionary of file extensions and their corresponding MIME types.
"""

GROUP_ID = {
    1:	"Avian Research",
    2:	"Fish and Wildlife Health",
    3:	"Freshwater Fisheries Biology",
    4:	"Habitat Research",
    5:	"Harmful Algal Blooms Research",
    6:	"Center for Spatial Analysis",
    7:	"Keys Fisheries Research",
    8:	"Marine Fisheries Biology",
    10:	"Marine Fisheries Dependent Monitoring",
    12:	"Marine Fisheries Independent Monitoring",
    13:	"Marine Fisheries Stock Assessment",
    14:	"Marine Fisheries Stock Enhancement Research",
    15:	"Marine Mammal Research",
    17:	"Terrestrial Mammal Research",
    18:	"Marine Turtle Research",
    19:	"Freshwater Resource Assessment",
    20:	"Reptiles and Amphibians Research",
    24:	"Center for Biostatistics and Modeling",
    25:	"Information Access",
    26:	"Socioeconomic Assessment",
    27:	"Aquatic Habitat Conservation Restoration",
    28:	"Imperiled Species Management",
    29:	"Species Conservation Planning",
    30:	"Invasive Plant Management",
    31:	"Conservation Planning Services",
    32:	"Wildlife and Habitat Management",
    33:	"Florida's Wildlife Legacy Initiative",
    34:	"Public Access Services Office",
    35:	"Wildlife Impact Management",
    36:	"Wildlife Diversity Conservation (SCP and FWLI)",
}
"""
A dictionary of FWC subunit IDs.
This will be moved to a configuration file.
"""

