import json
from pathlib import Path
from logging import getLogger
from logging.config import dictConfig

global CN_URL
CN_URL = "https://cn-stage.test.dataone.org/cn"

global DATA_ROOT
DATA_ROOT = Path('')

global CONFIG
CONFIG = {
    "rightsholder_orcid": "http://orcid.org/0000-0001-5828-6070",
    "nodeid": "urn:node:mnTestKNB",
    "mnurl": "https://dev.nceas.ucsb.edu/knb/d1/mn/",
    "cnurl": "https://cn-stage.test.dataone.org/cn",
    "metadata_json": "~/figshare-import/article-details-test.json",
    "data_root": "/mnt/ceph/repos/si/figshare/FIG-12/"
}

CONFIG_LOC = Path('~/.config/figshare-import/').expanduser().absolute()
LOGCONFIG = CONFIG_LOC.joinpath('log/config.json')
with open(LOGCONFIG, 'r') as lc:
    LOGGING_CONFIG = json.load(lc)
dictConfig(LOGGING_CONFIG)
WORK_LOC = Path('~/figshare-import/').expanduser().absolute()

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
    '.gpx': 'application/gpx+xml'
}

GROUP_ID = {
    46785: "CFCH",
    23468: "MCI",
    23471: "NASM",
    35808: "NMAA",
    23477: "NMNH",
    23492: "NMAH",
    28985: "NMAI",
    23474: "NZSCBI",
    23480: "OCIO",
    48638: "OIR",
    23483: "SERC",
    23489: "SLA",
    23486: "STRI",
    23417: "Smithsonian Research Data"
}

DEFAULT_CONTEXT = 'figshare'

def define_context(context: str=DEFAULT_CONTEXT):
    '''
    '''
    L = getLogger(__name__)
    path = Path(f'~/bin/figshare-import/figshare_import/manifest/{context}.jsonld').expanduser()
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    else:
        path = Path(f'{context}').expanduser()
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
        else:
            path = Path(f'~/bin/figshare-import/figshare_import/manifest/{DEFAULT_CONTEXT}.jsonld').expanduser()
            with open(path, 'r') as f:
                return json.load(f)


SO_TYPES = {
    "dataset": "Dataset",
    "figure": "Dataset",
    "preprint": "ScholarlyAricle",
    "book": "Book",
    "software": "SoftwareApplication",
    "media": "MediaObject"
}


SO_TEMPLATE = {
    "@context": {
        "@vocab": "https://schema.org/"
    },
    "type": "Dataset",
    "conditionsOfAccess": "unrestricted",
    "isAccessibleForFree": True,
    "id": "",
    "creator": {"@list": []},
    "datePublished": "",
    "description": {
        "@type": "text",
        "@value": ""
    },
    "distribution": [
        {
            "@type": "DataDownload",
            "contentUrl": "",
            "encodingFormat": ""
        }
    ],
    "funder": [],
    "identifier": {
        "@type": "PropertyValue",
        "propertyID": "https://registry.identifiers.org/registry/doi",
        "url": "",
        "value": ""
    },
    "keywords": [],
    "license": {'type': "CreativeWork"},
    "name": "",
    "spatialCoverage": {
        "geo": [
            {
                "@type": "GeoShape",
                "box": "",
            },
        ]
    },
    "version": "",
}


TEMP_ARTICLE = {
      "files": [
        {
          "id": 44937931,
          "name": "BayofPanama_Site1.zip",
          "size": 19891019,
          "is_link_only": False,
          "download_url": "https://ndownloader.figshare.com/files/44937931",
          "supplied_md5": "36fbce3d5c4ddd63c91a69801b6d15d2",
          "computed_md5": "36fbce3d5c4ddd63c91a69801b6d15d2",
          "mimetype": "application/zip"
        }
      ],
      "custom_fields": [],
      "authors": [
        {
          "id": 7540937,
          "full_name": "Steven Paton",
          "is_active": True,
          "url_name": "Steven_Paton",
          "orcid_id": "0000-0003-2035-6699"
        }
      ],
      "figshare_url": "https://smithsonian.figshare.com/articles/dataset/Bay_of_Panama_Water_Quality_Monitoring_Project_Site_1_of_7/10042703",
      "download_disabled": False,
      "description": "<div>Bay of Panama water quality monitoring program. Site #1 (of 7). <br></div><div>Location: 8° 38.743'N, 79° 2.887'W<br></div>Weekly depth profile (approximately 5m intervals) using YSI EXO 2 sonde. <br>Parameters measured temperature, salinity, conductivity, pH, turbidity, chlorophyll, Dissolved Oxygen<p></p>",
      "funding": None,
      "funding_list": [],
      "version": 5,
      "status": "public",
      "size": 19891019,
      "created_date": "2024-03-08T14:44:22Z",
      "modified_date": "2024-03-08T14:44:22Z",
      "is_public": True,
      "is_confidential": False,
      "is_metadata_record": False,
      "confidential_reason": "",
      "metadata_reason": "",
      "license": {
        "value": 1,
        "name": "CC BY 4.0",
        "url": "https://creativecommons.org/licenses/by/4.0/"
      },
      "tags": [
        "temperature",
        "salinity",
        "turbidity measurement",
        "chlorophyll",
        "conductivity",
        "Acidity",
        "Dissolved Oxygen",
        "Dissolved organic matter (DOM)",
        "Environmental Monitoring",
        "Physical Oceanography"
      ],
      "categories": [
        {
          "id": 26935,
          "title": "Environmental assessment and monitoring",
          "parent_id": 26929,
          "path": "/26863/26929/26935",
          "source_id": "410402",
          "taxonomy_id": 100
        },
        {
          "id": 25906,
          "title": "Physical oceanography",
          "parent_id": 25897,
          "path": "/25717/25897/25906",
          "source_id": "370803",
          "taxonomy_id": 100
        }
      ],
      "references": [
        "https://biogeodb.stri.si.edu/physical_monitoring/research/waterquality"
      ],
      "has_linked_file": False,
      "citation": "Paton, Steve (2019). Bay of Panama Water Quality Monitoring Project, Site 1 of 7. Smithsonian Tropical Research Institute. Dataset. https://doi.org/10.25573/data.10042703.v5",
      "related_materials": [
        {
          "id": 113195580,
          "identifier": "https://biogeodb.stri.si.edu/physical_monitoring/research/waterquality",
          "title": "",
          "relation": "References",
          "identifier_type": "URL",
          "is_linkout": False,
          "link": "https://biogeodb.stri.si.edu/physical_monitoring/research/waterquality"
        }
      ],
      "is_embargoed": False,
      "embargo_date": None,
      "embargo_type": "file",
      "embargo_title": "",
      "embargo_reason": "",
      "embargo_options": [],
      "id": 10042703,
      "title": "Bay of Panama Water Quality Monitoring Project, Site 1 of 7",
      "doi": "10.25573/data.10042703.v5",
      "handle": "",
      "url": "https://api.figshare.com/v2/articles/10042703",
      "published_date": "2024-03-08T14:44:22Z",
      "thumb": "",
      "defined_type": 3,
      "defined_type_name": "dataset",
      "group_id": 23486,
      "url_private_api": "https://api.figshare.com/v2/account/articles/10042703",
      "url_public_api": "https://api.figshare.com/v2/articles/10042703",
      "url_private_html": "https://figshare.com/account/articles/10042703",
      "url_public_html": "https://smithsonian.figshare.com/articles/dataset/Bay_of_Panama_Water_Quality_Monitoring_Project_Site_1_of_7/10042703",
      "timeline": {
        "posted": "2024-03-08T14:44:22",
        "firstOnline": "2019-10-28T12:51:31"
      },
      "resource_title": None,
      "resource_doi": None
    }
