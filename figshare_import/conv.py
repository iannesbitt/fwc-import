import logging
import d1_client.mnclient as mn
from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree

from .utils import parse_name, get_lat_lon, get_filelist


def figshare_to_eml(figshare: dict):
    
    eml = Element('eml:eml', attrib={
        'xmlns:eml': 'eml://ecoinformatics.org/eml-2.1.1',
        'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'xsi:schemaLocation': 'eml://ecoinformatics.org/eml-2.1.1 eml.xsd',
        'packageId': figshare['id'],
        'system': 'figshare'
    })
    
    dataset = SubElement(eml, 'dataset')
    
    title = SubElement(dataset, 'title')
    title.text = figshare['title']
    
    for author in figshare['authors']:
        creator = SubElement(dataset, 'creator')
        individualName = SubElement(creator, 'individualName')
        givenName = SubElement(individualName, 'givenName')
        given, family = parse_name(author['full_name'])
        givenName.text = given
        surName = SubElement(individualName, 'surName')
        surName.text = family
    
    pubDate = SubElement(dataset, 'pubDate')
    pubDate.text = figshare['published_date']
    
    abstract = SubElement(dataset, 'abstract')
    para = SubElement(abstract, 'para')
    para.text = figshare['description']
    
    intellectualRights = SubElement(dataset, 'intellectualRights')
    para = SubElement(intellectualRights, 'para')
    para.text = f"{figshare['license']['name']} ({figshare['license']['url']})"
    
    for file in figshare['files']:
        distribution = SubElement(dataset, 'distribution')
        online = SubElement(distribution, 'online')
        url = SubElement(online, 'url')
        url.text = file['download_url']
        description = SubElement(online, 'description')
        description.text = file['name']
    
    latlon_pairs = get_lat_lon(figshare['description'])
    if latlon_pairs:
        coverage = SubElement(dataset, 'coverage')
        geographicCoverage = SubElement(coverage, 'geographicCoverage')
        
        for latlon in latlon_pairs:
            boundingCoordinates = SubElement(geographicCoverage, 'boundingCoordinates')
            
            westBoundingCoordinate = SubElement(boundingCoordinates, 'westBoundingCoordinate')
            westBoundingCoordinate.text = str(latlon.lon)
            
            eastBoundingCoordinate = SubElement(boundingCoordinates, 'eastBoundingCoordinate')
            eastBoundingCoordinate.text = str(latlon.lon)
            
            northBoundingCoordinate = SubElement(boundingCoordinates, 'northBoundingCoordinate')
            northBoundingCoordinate.text = str(latlon.lat)
            
            southBoundingCoordinate = SubElement(boundingCoordinates, 'southBoundingCoordinate')
            southBoundingCoordinate.text = str(latlon.lat)

    return tostring(eml, encoding='unicode')
