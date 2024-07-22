import json
from pathlib import Path
from logging import getLogger

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
        "geo": {
            "@type": "GeoShape",
            "box": "",
            "name": ""
        },
    },
    "version": "",
}


TEMP_ARTICLE = {
    "files": [
        {
        "id": 21729828,
        "name": "Hall et al mature forest data used in Boeschoten et al_Framework species approach .xls",
        "size": 400896,
        "is_link_only": False,
        "download_url": "https://ndownloader.figshare.com/files/21729828",
        "supplied_md5": "19a59a83d90f352afc0c54b0ade4bc06",
        "computed_md5": "19a59a83d90f352afc0c54b0ade4bc06",
        "mimetype": "application/vnd.ms-excel"
        },
        {
        "id": 21729828,
        "name": "Hall-et-al.xls",
        "size": 400896,
        "is_link_only": False,
        "download_url": "https://ndownloader.figshare.com/files/21729829",
        "supplied_md5": "19a59a83d90f352afc0c54b0ade4bc060",
        "computed_md5": "19a59a83d90f352afc0c54b0ade4bc060",
        "mimetype": "application/vnd.ms-excel"
        }
    ],
    "custom_fields": [],
    "authors": [
        {
        "id": 8451984,
        "full_name": "Jefferson Hall",
        "is_active": True,
        "url_name": "Jefferson_Hall",
        "orcid_id": "0000-0003-4761-9268"
        },
        {
        "id": 4912528,
        "full_name": "Mario Baillon",
        "is_active": False,
        "url_name": "_",
        "orcid_id": ""
        },
        {
        "id": 8452001,
        "full_name": "Johana Balbuena",
        "is_active": False,
        "url_name": "_",
        "orcid_id": "0000-0002-1857-1560"
        },
        {
        "id": 8452007,
        "full_name": "Miguel Nuñez",
        "is_active": False,
        "url_name": "_",
        "orcid_id": "0000-0002-4408-9954"
        },
        {
        "id": 8452018,
        "full_name": "Arturo Cerezo",
        "is_active": False,
        "url_name": "_",
        "orcid_id": "0000-0003-3609-4013"
        },
        {
        "id": 4912456,
        "full_name": "Michiel van  Breugel",
        "is_active": True,
        "url_name": "Michiel_van_Breugel",
        "orcid_id": ""
        },
        {
        "id": 8452020,
        "full_name": "Laura E. Boeschoten",
        "is_active": False,
        "url_name": "_",
        "orcid_id": "0000-0002-6061-2194"
        }
    ],
    "figshare_url": "https://smithsonian.figshare.com/articles/dataset/Hall_et_al_data_used_in_data_from_Boeschoten_et_al_Framework_species_approach_2_of_2/11856180",
    "download_disabled": False,
    "description": "Mature forest data set used in Journal of Sustainable Forestry manuscript by Boeschoten et al. Reforestation data set uploaded separately.",
    "funding": None,
    "funding_list": [],
    "version": 1,
    "status": "public",
    "size": 400896,
    "created_date": "2020-04-29T19:43:27Z",
    "modified_date": "2020-04-29T19:43:45Z",
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
        "Panama Canal Watershed",
        "Forest Restoration",
        "Tropical Forest",
        "Plant Biology"
    ],
    "categories": [
        {
        "id": 24394,
        "title": "Plant biology not elsewhere classified",
        "parent_id": 24373,
        "path": "/24130/24373/24394",
        "source_id": "310899",
        "taxonomy_id": 100
        }
    ],
    "references": [],
    "has_linked_file": False,
    "citation": "Hall, Jefferson; Baillon, Mario; Balbuena, Johana; Nuñez, Miguel; Cerezo, Arturo; van  Breugel, Michiel; et al. (2020). Hall et al data used in data from Boeschoten et al_Framework species approach_2 of 2. Smithsonian Tropical Research Institute. Dataset. https://doi.org/10.25573/data.11856180.v1",
    "related_materials": [],
    "is_embargoed": False,
    "embargo_date": None,
    "embargo_type": "file",
    "embargo_title": "",
    "embargo_reason": "",
    "embargo_options": [],
    "id": 11856180,
    "title": "Hall et al data used in data from Boeschoten et al_Framework species approach_2 of 2",
    "doi": "10.25573/data.11856180.v1",
    "handle": "",
    "url": "https://api.figshare.com/v2/articles/11856180",
    "published_date": "2020-04-29T19:43:27Z",
    "thumb": "",
    "defined_type": 3,
    "defined_type_name": "dataset",
    "group_id": 23486,
    "url_private_api": "https://api.figshare.com/v2/account/articles/11856180",
    "url_public_api": "https://api.figshare.com/v2/articles/11856180",
    "url_private_html": "https://figshare.com/account/articles/11856180",
    "url_public_html": "https://smithsonian.figshare.com/articles/dataset/Hall_et_al_data_used_in_data_from_Boeschoten_et_al_Framework_species_approach_2_of_2/11856180",
    "timeline": {
        "posted": "2020-04-29T19:43:27",
        "firstOnline": "2020-04-29T19:43:27"
    },
    "resource_title": None,
    "resource_doi": None
    }
