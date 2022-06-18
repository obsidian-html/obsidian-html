# will return (False, False) if not found, (str:url, fo:file_object) when found
def FindFile(files, link, pb):

    if '://' not in link and (len(link.split('.')) == 1 or link.split('.')[-1] not in (pb.gc('included_file_suffixes', cached=True) + ['html', 'md'])):
        link += '.md'

    # return immediately if exact link is found in the array
    if link in files.keys():
        return (link, files[link])

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
    
    if len(matches) == 0:
        #print(link, '--> not_created.md')
        return (False, False)

    if len(matches) == 1:
        return (matches[0], files[matches[0]])

    # multiple matches found, sort on number of parts that matched
    # e.g. 'folder/home' will rank higher than 'home'
    matches = sorted(matches, key=lambda x: len(x.split('/')),reverse=True)
    return (matches[0], files[matches[0]])
        
