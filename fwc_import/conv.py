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

def build_eml(row, crosswalk):
    EML_NS = 'https://eml.ecoinformatics.org/eml-2.2.0'
    ET.register_namespace('eml', EML_NS)
    eml_root = ET.Element(f'{{{EML_NS}}}eml')
    for col, eml_path in crosswalk.items():
        value = str(row.get(col, '')).replace(' 00:00:00', '')
        if col == "SubunitID":
            value = SUBUNIT.get(int(value), value)
        if pd.isna(value) or str(value).strip().lower() in ('', 'nan', 'nat'):
            continue
        # Handle list of paths or single path
        paths = eml_path if isinstance(eml_path, list) else [eml_path]
        for path in paths:
            path_parts = path.split('/')
            leaf = ensure_path(eml_root, path_parts)
            leaf.text = clean_xml_text(value)
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
                write_pretty_xml(eml_tree, os.path.join(OUTPUT_DIR, filename))


if __name__ == '__main__':
    main()
