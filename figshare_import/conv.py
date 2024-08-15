from logging import getLogger
import d1_client.mnclient as mn
from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree
from html2text import html2text

from .utils import parse_name, get_lat_lon, get_article_list, write_article, fix_datetime
from .defs import GROUP_ID


def figshare_to_eml(figshare: dict):
    """
    Construct a minimal EML document from a figshare article.

    :param figshare: The figshare article data.
    :type figshare: dict
    :return: The EML-formatted string.
    :rtype: str
    """
    L = getLogger(__name__)
    L.info('Generating EML...')
    # Create the root element
    eml = Element('eml:eml', attrib={
        'xmlns:eml': 'https://eml.ecoinformatics.org/eml-2.2.0',
        'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'xsi:schemaLocation': 'https://eml.ecoinformatics.org/eml-2.2.0 https://eml.ecoinformatics.org/eml-2.2.0/eml.xsd',
        'packageId': f"doi:{figshare['doi']}",
        'system': 'https://si.edu',
    })
    # Create the dataset element
    dataset = SubElement(eml, 'dataset')
    # Create the alternateIdentifier element using the dataset DOI
    id = SubElement(dataset, 'alternateIdentifier')
    id.text = figshare['figshare_url']
    # Create the title element
    title = SubElement(dataset, 'title')
    title.text = figshare['title']
    # Create the creator element(s) from the author list
    L.info(f"Found {len(figshare['authors'])} authors")
    for author in figshare['authors']:
        creator = SubElement(dataset, 'creator')
        individualName = SubElement(creator, 'individualName')
        givenName = SubElement(individualName, 'givenName')
        author['givenName'], author['surName'] = parse_name(author['full_name'])
        givenName.text = author["givenName"]
        surName = SubElement(individualName, 'surName')
        surName.text = author["surName"]
        if ('orcid_id' in author) and (author['orcid_id'] != ''):
            userId = SubElement(creator, 'userId', directory='https://orcid.org')
            userId.text = author['orcid_id']
        L.info(f'Added author: {author["givenName"]} {author["surName"]}')
    # Create the pubDate element using the figshare published date
    pubDate = SubElement(dataset, 'pubDate')
    pubDate.text = fix_datetime(figshare['published_date'])
    # Create the abstract element using the figshare description
    abstract = SubElement(dataset, 'abstract')
    try:
        abs_text = html2text(figshare['description'])
        markdown = SubElement(abstract, 'markdown')
        markdown.text = abs_text
    except Exception as e:
        L.error(f'Error converting HTML to text: {repr(e)}')
        para = SubElement(abstract, 'para')
        para.text = figshare['description']
    # Create the keywordSet element and keyword(s) using the figshare tags list
    L.info(f"Found {len(figshare['tags'])} keyword tags in the article")
    keywordSet = SubElement(dataset, 'keywordSet')
    for keyword in figshare['tags']:
        keyword_element = SubElement(keywordSet, 'keyword')
        keyword_element.text = keyword
    # Add additionalInfo stating that this document was imported from figshare
    additionalInfo = SubElement(dataset, 'additionalInfo')
    para = SubElement(additionalInfo, 'para')
    para.text = """This metadata record was imported from Figshare using an automated process.
    The original metadata used for creating this record is preserved as a JSON file in this data package.
    Errors should be reported to the repository administrator."""
    # Create the intellectualRights element using the license name and URL
    intellectualRights = SubElement(dataset, 'intellectualRights')
    para = SubElement(intellectualRights, 'para')
    para.text = f"{figshare['license']['name']} ({figshare['license']['url']})"
    # add coverage elements
    coverage = None
    # Create the geographic coverage element(s) using the spatial coverage derived from the figshare description
    latlon_pairs = get_lat_lon(figshare['description'])
    if latlon_pairs:
        L.info(f'Found {len(latlon_pairs)} geographic coverage value(s) in article description')
        coverage = SubElement(dataset, 'coverage')
        for latlon in latlon_pairs:
            if (latlon.lat > 90) or (latlon.lat < -90) or (latlon.lon > 180) or (latlon.lon < -180):
                L.warning(f'Invalid latitude/longitude pair: {latlon.lat}, {latlon.lon}')
                continue
            # Create a geographicCoverage element for each lat/lon pair
            geographicCoverage = SubElement(coverage, 'geographicCoverage')
            geographicDescription = SubElement(geographicCoverage, 'geographicDescription')
            geographicDescription.text = 'Bounding coordinate derived from article description'
            boundingCoordinates = SubElement(geographicCoverage, 'boundingCoordinates')
            # West
            westBoundingCoordinate = SubElement(boundingCoordinates, 'westBoundingCoordinate')
            westBoundingCoordinate.text = str(latlon.lon)
            # East
            eastBoundingCoordinate = SubElement(boundingCoordinates, 'eastBoundingCoordinate')
            eastBoundingCoordinate.text = str(latlon.lon)
            # North
            northBoundingCoordinate = SubElement(boundingCoordinates, 'northBoundingCoordinate')
            northBoundingCoordinate.text = str(latlon.lat)
            # South
            southBoundingCoordinate = SubElement(boundingCoordinates, 'southBoundingCoordinate')
            southBoundingCoordinate.text = str(latlon.lat)
    if False:
        # not yet implemented
        if not coverage:
            coverage = SubElement(dataset, 'coverage')
        temporalCoverage = SubElement(coverage, 'temporalCoverage')
    # Create the contact element using the first author's givenName and surName
    contact = SubElement(dataset, 'contact')
    individualName = SubElement(contact, 'individualName')
    givenName = SubElement(individualName, 'givenName')
    givenName.text = figshare['authors'][0]['givenName']
    surName = SubElement(individualName, 'surName')
    surName.text = figshare['authors'][0]['surName']
    if ('orcid_id' in figshare['authors'][0]) and (figshare['authors'][0]['orcid_id'] != ''):
        userId = SubElement(contact, 'userId', directory='https://orcid.org')
        userId.text = figshare['authors'][0]['orcid_id']
    # Create the publisher element using the group ID mapping
    publisher = SubElement(dataset, 'publisher')
    organization = SubElement(publisher, 'organizationName')
    organization.text = GROUP_ID[figshare.get('group_id', 23417)]
    # Create the entity element(s) using the figshare files list
    L.debug(f"figshare['files'] before EML serialization: {figshare.get('files')}")
    L.info(f"Found {len(figshare['files'])} file(s) in the article")
    for file in figshare['files']:
        if False:
            # not yet implemented
            file_extensions = ['.shp', '.geojson', '.kml', '.gpx']
            if any(ext in file['name'] for ext in file_extensions):
                etype = 'spatialVector'
            file_extensions = ['.tif', '.tiff', '.geotiff']
            if any(ext in file['name'] for ext in file_extensions):
                etype = 'spatialRaster'
            file_extensions = ['.csv', '.txt', '.xls', '.xlsx', '.tsv']
            if any(ext in file['name'] for ext in file_extensions):
                etype = 'dataTable'
        else:
            etype = 'otherEntity'
        entity = SubElement(dataset, etype, id=file['pid'])
        entityName = SubElement(entity, 'entityName')
        entityName.text = file['name']
        if etype == 'otherEntity':
            entityType = SubElement(entity, 'entityType')
            entityType.text = file['mimetype']
        else:
            entityAdditionalInfo = SubElement(entity, 'additionalInfo')
            para = SubElement(entityAdditionalInfo, 'para')
            para.text = f"File type: {file['mimetype']}"
    L.info('EML generation complete')
    return tostring(eml, encoding='unicode')


def process_articles(articles: dict):
    """
    This function performs three actions:

    1. Writes the original Figshare metadata to files in JSON format.
    2. Converts the Figshare metadata to EML-formatted strings.
    3. Writes the EML to XML.
    Archives Figshare articles by writing them to files in different formats.

    :note:
        This function is intended only to write Figshare articles to JSON and
        convert them to EML/XML. It does not upload the EML to a DataONE
        Member Node.

    :param articles: The data containing articles.
    :type articles: dict
    :return: A list of processed articles in EML format.
    :rtype: dict
    """
    L = getLogger(__name__)
    articles = get_article_list(articles)
    eml_list = []
    i = 0
    for article in articles:
        L.debug(f'Starting record {i}')
        write_article(article, fmt='json', doi=article.get('doi'), title=article.get('title'))
        eml = figshare_to_eml(article)
        write_article(eml, fmt='xml', doi=article.get('doi'), title=article.get('title'))
        eml_list.append(eml)
        i += 1
    return eml_list
