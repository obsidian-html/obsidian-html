from functools import cache
from bs4 import BeautifulSoup

from ..lib import OpenIncludedFile, expect_list


def get_side_pane_html(pb, pane_id, node):
    """This function gets the HTML for either the left or right pane"""

    if not pb.gc(f"toggles/features/side_pane/{pane_id}/enabled"):
        return ""

    content = get_side_pane_content(pb, pane_id, node)
    template = OpenIncludedFile(f"html/templates/{pane_id}.html")
    template = template.replace("{content}", content)

    return template


def get_side_pane_content(pb, pane_id, node):
    content_selector = pb.gc(f"toggles/features/side_pane/{pane_id}/contents")

    if content_selector == "toc":
        return ""

    if content_selector == "tag_tree":
        # if "tags_page_html" not in pb.jars.keys():
        #     raise Exception("Make sure that you have enabled the feature create_index_from_tags and that it isnt used as the homepage! tags_page_html not found in jars")
        # return '<div class="tags-pane-content">' + pb.jars["tags_page_html"] + "</div>"
        from ..compiler.HTML import create_foldable_tag_lists_html

        strip_tags = tuple(pb.gc(f"toggles/features/side_pane/{pane_id}/content_args/strip_tags"))
        html = create_foldable_tag_lists_html(pb, strip_tags)
        return '<div class="tags-pane-content">' + html + "</div>"

    if content_selector == "dir_tree":
        pb.EnsureTreeObj()
        dir_list = pb.treeobj.BuildIndex(current_page=node["url"])
        return dir_list

    if content_selector == "html_page":
        return get_html_page_content(pb, pane_id)

    return ""


@cache
def get_html_page_content(pb, pane_id):
    # get args
    content_args = pb.gc(f"toggles/features/side_pane/{pane_id}/content_args")
    if not bool(content_args):
        raise Exception(f"html_page selected for {pane_id} but no content_args were provided")

    file_rtr = content_args["rel_path"]
    div_selector = ".container"
    if "div_selector" in content_args:
        div_selector = content_args["div_selector"]

    div_selector, div_attr_type = parse_div_selector(div_selector)

    # get file and convert to soup
    fo = pb.index.fo_by_html_relpath[file_rtr]
    dst_abs_path = fo.path["html"]["file_absolute_path"]
    with open(dst_abs_path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, features="html5lib")

    # Get div contents
    div = soup.find("div", attrs={div_attr_type: div_selector})

    # strip script tags
    for s in div.select("script"):
        s.extract()

    # strip script tags
    for strip_selector in content_args["strip_sub_divs"]:
        div_selector, div_attr_type = parse_div_selector(strip_selector)
        for s in expect_list(div.find_all("div", attrs={div_attr_type: div_selector})):
            s.extract()

    # wrap content so we can give it proper padding in css
    output = f'<div class="side-pane-container">{str(div)}</div>'

    return output


def parse_div_selector(sel):
    if sel[0] == "#":
        attr_type = "id"
    elif sel[0] == ".":
        attr_type = "class"
    else:
        raise Exception(f'Could not determine attr type from selector {sel}. Selector should start with "." or "#".')

    return sel[1:], attr_type


def get_side_pane_id_by_content_selector(pb, content_selector):
    # no side panes available when no documentation layout is selected
    if pb.gc("toggles/features/styling/layout") in ["tabs", "no_tabs", "minimal"]:
        return ""

    if content_selector == pb.gc("toggles/features/side_pane/left_pane/contents"):
        if pb.gc("toggles/features/side_pane/left_pane/enabled"):
            return "left_pane_content"
        else:
            return ""
    if content_selector == pb.gc("toggles/features/side_pane/right_pane/contents"):
        if pb.gc("toggles/features/side_pane/right_pane/enabled"):
            return "right_pane_content"
        else:
            return ""
    return ""


def get_content_name_by_pane_id(pb, pane_id):
    names = {"toc": "Table of Contents", "dir_tree": "Directory Tree", "tag_tree": "Tag Tree", "html_page": pane_id.split("_")[0].title()}
    content_key = pb.gc(f"toggles/features/side_pane/{pane_id}/contents")
    if content_key not in names.keys():
        return pane_id
    return names[content_key]
