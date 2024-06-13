from logging import getLogger

def parse_name(fullname: str):
    """
    Parse full names into given and family designations.
    """
    given, family = None, None
    if ', ' in fullname:
        [family, given] = fullname.title().split(', ')[:2]
    if (given == None) and (family == None):
        for q in [' del ', ' van ']:
            if q in fullname.lower():
                [given, family] = fullname.lower().split(q)
                given = given.title()
                family = f'{q.strip()}{family.title()}'
    if (given == None) and (family == None):
        nlist = fullname.title().split()
        family = nlist[-1]
        if len(nlist) > 2:
            given = nlist[0]
            for i in range(1, len(nlist)-1):
                given = f'{given} {nlist[i]}'
    if (not given) or (not family):
        L = getLogger()
        L.warning(f'Could not parse name "{fullname}". Result of given name: "{given}" Family name: "{family}"')
    return given, family
