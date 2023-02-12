import regex as re          # regex string finding/replacing
import urllib.parse         # convert link characters like %

# -- [3] Convert Obsidian type img links to proper md image links
# Further conversion will be done in the block below
def obs_img_to_md_img(pb, page):
    for matched_link in re.findall("(?<=\!\[\[)(.*?)(?=\]\])", page):
        link = ''
        if '|' in matched_link:
            parts = matched_link.split('|')
            link = parts.pop(0)
            alias = '|'.join(parts)
            new_link = f'![{alias}]('+urllib.parse.quote(link)+')'
        else:
            new_link = '![]('+urllib.parse.quote(matched_link)+')'

        # Obsidian page inclusions use the same tag...
        # Skip if we don't match image suffixes. Inclusions are handled at the end.
        link = matched_link.split('|')[0]
        if len(link.split('.')) == 1 or link.split('.')[-1].lower() not in pb.gc('included_file_suffixes', cached=True):
            new_link = f'<inclusion href="{link}" />'

        safe_link = re.escape('![['+matched_link+']]')
        page = re.sub(safe_link, new_link, page)
        
    return page