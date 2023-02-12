import regex as re          # regex string finding/replacing
import urllib.parse         # convert link characters like %

# -- [3] Convert Obsidian type img links to proper md image links
# Further conversion will be done in the block below
def obs_img_to_md_img(pb, page):
    for link in re.findall("(?<=\!\[\[)(.*?)(?=\]\])", page):
        if '|' in link:
            parts = link.split('|')
            l = parts.pop(0)
            alias = '|'.join(parts)
            new_link = f'![{alias}]('+urllib.parse.quote(l)+')'
        else:
            new_link = '![]('+urllib.parse.quote(link)+')'

        # Obsidian page inclusions use the same tag...
        # Skip if we don't match image suffixes. Inclusions are handled at the end.
        l = link.split('|')[0]
        if len(l.split('.')) == 1 or l.split('.')[-1].lower() not in pb.gc('included_file_suffixes', cached=True):
            new_link = f'<inclusion href="{l}" />'

        safe_link = re.escape('![['+link+']]')
        page = re.sub(safe_link, new_link, page)
        
    return page