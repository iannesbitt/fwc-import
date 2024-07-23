import logging
import pyld
from pygeodesy.dms import parse3llh
from pygeodesy.namedTuples import LatLon3Tuple

# from metapype.eml.exceptions import MetapypeRuleError
# import metapype.eml.names as names
# import metapype.eml.validate as validate
# from metapype.model.node import Node

from .defs import define_context, TEMP_ARTICLE, SO_TEMPLATE


def from_scratch_eml():
    """
    This would be a way to generate EML from scratch.
    We are ignoring this for now in order to use the codemeta crosswalk method
    (https://github.com/codemeta/codemeta/).
    """

    eml = Node(names.EML)
    eml.add_attribute('packageId', 'edi.23.1')
    eml.add_attribute('system', 'metapype')

    access = Node(names.ACCESS, parent=eml)
    access.add_attribute('authSystem', 'pasta')
    access.add_attribute('order', 'allowFirst')
    eml.add_child(access)

    allow = Node(names.ALLOW, parent=access)
    access.add_child(allow)

    principal = Node(names.PRINCIPAL, parent=allow)
    principal.content = 'uid=gaucho,o=EDI,dc=edirepository,dc=org'
    allow.add_child(principal)

    permission = Node(names.PERMISSION, parent=allow)
    permission.content = 'all'
    allow.add_child(permission)

    dataset = Node(names.DATASET, parent=eml)
    eml.add_child(dataset)

    title = Node(names.TITLE, parent=dataset)
    title.content = 'Green sea turtle counts: Tortuga Island 20017'
    dataset.add_child(title)

    creator = Node(names.CREATOR, parent=dataset)
    dataset.add_child(creator)

    individualName_creator = Node(names.INDIVIDUALNAME, parent=creator)
    creator.add_child(individualName_creator)

    surName_creator = Node(names.SURNAME, parent=individualName_creator)
    surName_creator.content = 'Gaucho'
    individualName_creator.add_child(surName_creator)

    contact = Node(names.CONTACT, parent=dataset)
    dataset.add_child(contact)

    individualName_contact = Node(names.INDIVIDUALNAME, parent=contact)
    contact.add_child(individualName_contact)

    surName_contact = Node(names.SURNAME, parent=individualName_contact)
    surName_contact.content = 'Gaucho'
    individualName_contact.add_child(surName_contact)

    try:
        validate.tree(eml)
    except MetapypeRuleError as e:
        logging.error(e)
        
    return 0


def get_lat_lon(desc: str):
    """
    Get latitude and longitude from description if they exist
    """
    latlon = None
    if ("°" in desc) and (not "°C" in desc):
        latlon = []
        x = desc
        while True:
            ll = None
            try:
                i = x.index('°')
            except:
                break
            try:
                i2 = x[i-10:i].rindex('(')+i-10
            except:
                i2 = x[:i].rfind(' ')
            for fw in ["'W", '\"W' '°W', '°', '<']:
                try:
                    i3 = x[i2:i2+40].index(fw)+i2
                    ll: LatLon3Tuple = parse3llh(x[i2:i3])
                    if ll:
                        latlon.append(ll)
                        break
                except:
                    continue
            x = x[i3:]
    return latlon


def get_geoboxes(latlon: list[LatLon3Tuple]):
    """
    """
    geolist = []
    for ll in latlon:
        geolist.append({"@type": "GeoShape", "box": f"{ll.lat} {ll.lon} {ll.lat} {ll.lon}"})
    return geolist


def to_so(article: dict):
    """
    """
    so = SO_TEMPLATE
    so['id'] = f"https://doi.org/{article['doi']}"
    so['url'] = so['id']
    for c in article['authors']:
        creator = {}
        creator['name'] = c['full_name']
        orcid = c.get('orcid_id')
        if orcid:
            creator['url'] = f'http://orcid.org/{orcid}'
        else:
            url_name = c.get('url_name')
            if url_name and (url_name != "_"):
                creator['url'] = f'https://figshare.com/authors/{url_name}/{c['id']}'
        so['creator']['@list'].append(creator)
    so['datePublished'] = article['published_date']
    so['description']['@value'] = article['description']
    funders = article.get('funding_list')
    f = 0
    if len(funders) > 0:
        so['funder'].append({
            'type': 'Grant',
            'funder': {
                'name': funders[f].get('funder_name'),
                'type': 'Organization'
            },
            'identifier': funders[f]['grant_code'],
            'name': funders[f]['title'],
        })
        f += 1
    so['identifier']['url'] = so['url']
    so['identifier']['value'] = f'doi:{article['doi']}'
    so['keywords'] = article['tags']
    so['license']['text'] = article['license'].get('name')
    so['license']['url'] = article['license'].get('url')
    so['name'] = article['title']
    latlon = get_lat_lon(article['description'])
    geoboxes = get_geoboxes(latlon)
    if geoboxes:
        so['spatialCoverage']['geo'] = geoboxes
    so['version'] = article['version']


def frame(jld: dict, context: dict=define_context()):
    """
    """
    return pyld.jsonld.frame(jld, frame=context)


def compact(jld: dict, context: dict=define_context()):
    """
    """
    return pyld.jsonld.compact(jld, ctx=context)


def expand(jld: dict):
    """
    """
    return pyld.jsonld.expand(jld)

def frame(article: dict=TEMP_ARTICLE, context: dict=define_context()):
    """
    """
    article['@context'] = context
    return pyld.jsonld.frame(article, frame=context)
