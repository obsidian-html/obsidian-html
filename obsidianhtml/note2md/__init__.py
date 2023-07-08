import regex as re  # regex string finding/replacing
import urllib.parse  # convert link characters like %

from ..parser.HeaderTree import convert_markdown_to_header_tree


# -- [3] Convert Obsidian type img links to proper md image links
# Further conversion will be done in the block below
def obs_img_to_md_img(pb, page):
    for matched_link in re.findall("(?<=\!\[\[)(.*?)(?=\]\])", page):
        link = ""
        if "|" in matched_link:
            parts = matched_link.split("|")
            link = parts.pop(0)
            alias = "|".join(parts)
            new_link = f"![{alias}](" + urllib.parse.quote(link.split("#")[0]) + ")"
        else:
            new_link = "![](" + urllib.parse.quote(matched_link) + ")"

        # Obsidian page inclusions use the same tag...
        # Skip if we don't match image suffixes. Inclusions are handled at the end.
        link = matched_link.split("|")[0]
        link_without_hashtag = link.split("#")[0]
        if len(link.split(".")) == 1 or link_without_hashtag.split(".")[-1].lower() not in pb.gc("included_file_suffixes", cached=True):
            new_link = f'<inclusion href="{link}" />'

        safe_link = re.escape("![[" + matched_link + "]]")
        page = re.sub(safe_link, new_link, page)

    return page


def add_embedded_title(pb, page, note_metadata, note_name):
    if not pb.capabilities_needed["embedded_note_titles"]:
        return page

    if "obs.html.tags" in note_metadata.keys() and "dont_add_embedded_title" in note_metadata["obs.html.tags"]:
        return page

    title = note_name

    # overwrite node name (titleMetadataField)
    if "titleMetadataField" in pb.plugin_settings["embedded_note_titles"].keys():
        title_key = pb.plugin_settings["embedded_note_titles"]["titleMetadataField"]
        if title_key in note_metadata.keys():
            title = note_metadata[title_key]

    # hide if h1 is present
    hide = False
    if pb.gc("toggles/features/embedded_note_titles/hide_on_h1"):
        header_dict, root_element = convert_markdown_to_header_tree(page)
        if len(root_element["content"]) > 0 and isinstance(root_element["content"][0], dict) and root_element["content"][0]["level"] == 1:
            hide = True

    # hideOnMetadataField
    if "hideOnMetadataField" in pb.plugin_settings["embedded_note_titles"].keys() and pb.plugin_settings["embedded_note_titles"]["hideOnMetadataField"]:
        if "embedded-title" in note_metadata.keys() and note_metadata["embedded-title"] is False:
            hide = True

    # add embedded title
    if not hide:
        return f"# {title}\n" + page

    return page
