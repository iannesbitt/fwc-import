import os
import json
import pandas as pd
import xml.etree.ElementTree as ET
import xml.dom.minidom
import re

CROSSWALK_FILE = './fwc_import/manifest/fwc_crosswalk.json'
SHEETS_DIR = './fwc_import/manifest/meta'
OUTPUT_DIR = './output_eml'

SUBUNIT = {
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
"""

metadataProvider = {
    "organizationName": "Florida Fish and Wildlife Conservation Commission",
    "address": {
        "deliveryPoint": "620 S. Meridian St.",
        "city": "Tallahassee",
        "administrativeArea": "FL",
        "postalCode": "32399-1600",
        "country": "USA"
    },
    "phone": "+1 (850) 488-4676",
    "electronicMailAddress": "metadata@myfwc.com",
    "onlineUrl": "https://myfwc.com",
}


def hyphenate(text):
    # Lowercase, replace spaces and non-alphanum with hyphens
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def parse_segment(segment):
    """
    Parse a segment like "userId directory='https://orcid.org'" into
    ('userId', {'directory': 'https://orcid.org'})
    """
    tag_match = re.match(r"^\s*([^\s]+)", segment)
    tag = tag_match.group(1) if tag_match else segment.strip()
    attrs = dict(re.findall(r"([a-zA-Z0-9_:-]+)\s*=\s*'([^']*)'", segment))
    return tag, attrs

def ensure_path(root, path):
    """
    Walks/creates nodes along path, applies attributes, returns the leaf node.
    """
    node = root
    for segment in path:
        tag, attrs = parse_segment(segment)
        found = None
        # Try to find an existing child with the same tag and attributes
        for child in node.findall(tag):
            if all(child.get(k) == v for k, v in attrs.items()):
                found = child
                break
        if found is None:
            found = ET.SubElement(node, tag, attrib=attrs)
        node = found
    return node

def clean_xml_text(text):
    # Remove invalid XML 1.0 characters
    # See: https://stackoverflow.com/a/25920330/43839
    RE_XML_ILLEGAL = (
        u'([\u0000-\u0008\u000b\u000c\u000e-\u001f'
        u'\ud800-\udfff'
        u'\ufffe-\uffff])'
    )
    return re.sub(RE_XML_ILLEGAL, '', text)

def add_contact(parent):
    def sub(elem, tag, text, attrib=None):
        t = ET.SubElement(elem, tag, attrib=attrib or {})
        t.text = text
        return t

    mp_elem = ET.SubElement(parent, f'contact')
    sub(mp_elem, f'organizationName', metadataProvider["organizationName"])
    addr_elem = ET.SubElement(mp_elem, f'address')
    for k in ["deliveryPoint", "city", "administrativeArea", "postalCode", "country"]:
        sub(addr_elem, f'{k}', metadataProvider["address"][k])
    sub(mp_elem, f'phone', metadataProvider["phone"], attrib={"phonetype": "voice"})
    sub(mp_elem, f'electronicMailAddress', metadataProvider["electronicMailAddress"])
    sub(mp_elem, f'onlineUrl', metadataProvider["onlineUrl"])


def build_eml(row, crosswalk):
    EML_NS = 'https://eml.ecoinformatics.org/eml-2.2.0'
    XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'
    STMML_NS = 'http://www.xml-cml.org/schema/stmml-1.1'
    ET.register_namespace('eml', EML_NS)
    ET.register_namespace('xsi', XSI_NS)
    ET.register_namespace('stmml', STMML_NS)
    eml_root = ET.Element(
        f'{{{EML_NS}}}eml',
        {
            'xmlns:xsi': XSI_NS,
            'xmlns:stmml': STMML_NS,
            'system': 'knb'
        }
    )
    dataset_elem = ET.SubElement(eml_root, f'dataset')
    for col, eml_path in crosswalk.items():
        value = str(row.get(col, '')).replace(' 00:00:00', '')
        if col == "SubunitID":
            value = SUBUNIT.get(int(value), value)
        if col.lower() == "studyarea":
            value = "No description provided" if pd.isna(value) or str(value).strip().lower() in ('', 'nan', 'nat') else value
        if col.lower() == "principalinvestigator":
            # split name into givenName and surName
            if pd.notna(value) and str(value).strip().lower() not in ("", "nan", "nat"):
                names = value.split(' ')
                if len(names) == 2:
                    given_name, sur_name = names[0].strip(), names[1].strip()
                else:
                    given_name, sur_name = ' '.join(names[0:]).strip(), names[1].strip()
                creator_elem = ET.SubElement(dataset_elem, "creator")
                name_elem = ET.SubElement(creator_elem, "individualName")
                ET.SubElement(name_elem, "givenName").text = clean_xml_text(given_name)
                ET.SubElement(name_elem, "surName").text = clean_xml_text(sur_name)
            continue
        if pd.isna(value) or str(value).strip().lower() in ('', 'nan', 'nat'):
            continue
        # Handle list of paths or single path
        paths = eml_path if isinstance(eml_path, list) else [eml_path]
        for path in paths:
            path_parts = path.split('/')
            if (col.lower() == "description") or (isinstance(eml_path, str) and "abstract" in eml_path):
                leaf = ensure_path(eml_root, path_parts)
                # Remove any existing text
                leaf.text = None
                for para in filter(None, re.split(r'\r\n|\r|\n', value)):
                    para_elem = ET.SubElement(leaf, "para")
                    para_elem.text = clean_xml_text(para)
            else:
                leaf = ensure_path(eml_root, path_parts)
                leaf.text = clean_xml_text(value)
    add_contact(dataset_elem)
    # Special handling for DatasetID
    additionalInfo = ET.SubElement(dataset_elem, "additionalInfo")
    for dataset_col in ["DatasetID", "ProjectID", "SpatialResolution"]:
        title = dataset_col if "ID" in dataset_col else "Additional Information (FWC 'SpatialResolution' field)"
        value = row.get(dataset_col, "")
        if pd.notna(value) and str(value).strip().lower() not in ("", "nan", "nat"):
            title_elem = ET.SubElement(additionalInfo, "para")
            title_elem.text = f"{title}:"
            for para in filter(None, re.split(r'\r\n|\r|\n', value)):
                para_elem = ET.SubElement(additionalInfo, "para")
                para_elem.text = clean_xml_text(para)
    # Special handling for urls/alt identifiers
    for url_col in ["DatasetURL", "ProjectURL"]:
        url = row.get(url_col, "")
        if pd.notna(url) and str(url).strip().lower() not in ("", "nan", "nat"):
            annotation = ET.SubElement(dataset_elem, "annotation")
            prop_uri = ET.SubElement(annotation, "propertyURI", label="sameAs")
            prop_uri.text = "http://www.w3.org/2002/07/owl#sameAs"
            value_uri = ET.SubElement(annotation, "valueURI", label=str(url).strip())
            value_uri.text = str(url).strip()
    # Special handling for process fields
    method_step_elem = ET.SubElement(dataset_elem, "methods")
    for field in ["Completeness", "LogicalConsistencyRpt"]:
        value = row.get(field, '')
        if pd.isna(value) or str(value).strip().lower() in ('', 'nan', 'nat'):
            continue
        method_step = ET.SubElement(method_step_elem, "methodStep")
        desc_elem = ET.SubElement(method_step, "description")
        title_elem = ET.SubElement(desc_elem, "title")
        title_elem.text = field
        para_elem = ET.SubElement(desc_elem, "para")
        para_elem.text = clean_xml_text(str(value))
    return eml_root

def write_pretty_xml(element, filename):
    rough_string = ET.tostring(element, encoding='utf-8')
    reparsed = xml.dom.minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ", encoding='utf-8')
    with open(filename, 'wb') as f:
        f.write(pretty_xml)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(CROSSWALK_FILE) as f:
        crosswalk = json.load(f)

    for fname in os.listdir(SHEETS_DIR):
        if (('records_to' in fname) and fname.endswith('.xlsx')):
            df = pd.read_excel(os.path.join(SHEETS_DIR, fname), dtype=str)
            for _, row in df.iterrows():
                eml_tree = build_eml(row, crosswalk)
                # Use title or fallback as filename
                title_col = next((c for c in crosswalk if 'title' in c.lower()), None)
                title = row.get(title_col, 'untitled') if title_col else 'untitled'
                filename = hyphenate(str(title)) + '.xml'
                try:
                    write_pretty_xml(eml_tree, os.path.join(OUTPUT_DIR, filename))
                except Exception as e:
                    print(f"Error writing {filename}: {e}\n{ET.tostring(eml_tree, encoding='utf-8')}")
                    exit(1)


if __name__ == '__main__':
    main()
