from logging import getLogger
import d1_client.mnclient as mn
from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree

from .utils import parse_name, get_lat_lon, get_article_list, write_article
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
        'xmlns:eml': 'eml://ecoinformatics.org/eml-2.1.1',
        'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'xsi:schemaLocation': 'eml://ecoinformatics.org/eml-2.1.1 eml.xsd',
        'packageId': figshare['id'],
        'system': 'figshare'
    })
    # Create the dataset element
    dataset = SubElement(eml, 'dataset')
    # Create the title element
    title = SubElement(dataset, 'title')
    title.text = figshare['title']
    # Create the alternateIdentifier element using the dataset DOI
    id = SubElement(dataset, 'alternateIdentifier')
    id.text = figshare['doi']
    # Create the creator element(s) from the author list
    L.info(f"Found {len(figshare['authors'])} authors")
    for author in figshare['authors']:
        creator = SubElement(dataset, 'creator')
        individualName = SubElement(creator, 'individualName')
        givenName = SubElement(individualName, 'givenName')
        given, family = parse_name(author['full_name'])
        givenName.text = given
        surName = SubElement(individualName, 'surName')
        surName.text = family
        L.info(f'Added author: {given} {family}')
    # Create the organization element using the group ID mapping
    organization = SubElement(dataset, 'organizationName')
    organization.text = GROUP_ID[figshare.get('group_id', 23417)]
    # Create the pubDate element using the figshare published date
    pubDate = SubElement(dataset, 'pubDate')
    pubDate.text = figshare['published_date']
    # Create the abstract element using the figshare description
    abstract = SubElement(dataset, 'abstract')
    para = SubElement(abstract, 'para')
    para.text = figshare['description']
    # Create the intellectualRights element using the license name and URL
    intellectualRights = SubElement(dataset, 'intellectualRights')
    para = SubElement(intellectualRights, 'para')
    para.text = f"{figshare['license']['name']} ({figshare['license']['url']})"
    L.info(f"Found {len(figshare['tags'])} keyword tags in the article")
    # Create the keywordSet element and keyword(s) using the figshare tags list
    keywordSet = SubElement(dataset, 'keywordSet')
    for keyword in figshare['tags']:
        keyword_element = SubElement(keywordSet, 'keyword')
        keyword_element.text = keyword
    L.info(f"Found {len(figshare['files'])} file(s) in the article")
    # Create the distribution element(s) using the figshare files list
    for file in figshare['files']:
        distribution = SubElement(dataset, 'distribution')
        online = SubElement(distribution, 'online')
        url = SubElement(online, 'url')
        if file.get('d1_url'):
            url.text = file['d1_url']
        else:
            url.text = file['download_url']
        description = SubElement(online, 'description')
        description.text = file['name']
    # Create the geographic coverage element(s) using the spatial coverage derived from the figshare description
    latlon_pairs = get_lat_lon(figshare['description'])
    if latlon_pairs:
        L.info(f'Found {len(latlon_pairs)} geographic coverage value(s) in article description')
        coverage = SubElement(dataset, 'coverage')
        geographicCoverage = SubElement(coverage, 'geographicCoverage')
        # Create a boundingCoordinates element for each lat/lon pair
        for latlon in latlon_pairs:
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
