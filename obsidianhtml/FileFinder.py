# will return (False, False) if not found, (str:url, fo:file_object) when found
def FindFile(files, link, pb):
    if '://' not in link and (len(link.split('.')) == 1 or link.split('.')[-1] not in (pb.gc('included_file_suffixes', cached=True) + ['html', 'md'])):
        link += '.md'

    # remove leading ../ or ./
    if link[0:2] == './':
        link = link[2:]
    while link[0:3] == '../':
        link = link[3:]

    # remove leading html_url_prefix
    html_url_prefix = pb.gc('html_url_prefix')[1:]
    if html_url_prefix != '':
        if link.startswith(html_url_prefix):
            link = link.replace(html_url_prefix+'/', '', 1)

    # return immediately if exact link is found in the array
    if link in files.keys():
        return (link, files[link])

    # find all links that match the tail part
    matches = GetMatches(files, link)
    
    if len(matches) == 0:
        #print(link, '--> not_created.md')
        return (False, False)

    if len(matches) == 1:
        return (matches[0], files[matches[0]])

    # multiple matches found, sort on number of parts that matched
    # e.g. 'folder/home' will rank higher than 'home'
    matches = sorted(matches, key=lambda x: len(x.split('/')),reverse=True)
    return (matches[0], files[matches[0]])

def GetMatches(files, link):
    # find all links that match the tail part
    url_parts = link.split('/')
    matches = []
    for rel_path in files.keys():
        parts = rel_path.split('/')
        if len(url_parts) > len(parts):
            continue
        
        match = True
        for i in range(1, len(url_parts)+1):
            if url_parts[-i] != parts[-i]:
                match = False
                break
        if match:
            matches.append(rel_path)
    return matches
        
def GetNodeId(files, link):
    node_id = ''
    parts = link.split('/')
    for i in range(1, len(parts)+1):
        if node_id == '':
            node_id = parts[-i]
        else:
            node_id = f'{parts[-i]}/{node_id}'

        matches = GetMatches(files, node_id)
        if len(matches) == 1:
            if node_id[-3:] == ".md":
                node_id = node_id[:-3]
            return node_id
    raise Exception(f'No unique node id found for {link}') 
