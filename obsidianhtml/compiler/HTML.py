import markdown  # convert markdown to html
from functools import cache

from ..core import Types as T
from ..lib import get_rel_html_url_prefix, slugify_path, expect_list
from ..compiler.Templating import PopulateTemplate
from ..modules.lib import verbose_enough


def compile_navbar_links(pb) -> T.PBChange:
    """
    This function creates a block of html that defines the navigation links at the top of the page.
    These links are created based on the config yaml value for navbar_links
    """

    html_url_prefix = pb.gc("html_url_prefix")
    navbar_links = pb.gc("navbar_links", cached=True)
    elements = []

    for l in navbar_links:
        link = l["link"]
        el = None

        # external links
        if "type" in l.keys():
            if l["type"] == "external":
                el = f'<a class="navbar-link" href="{link}" title="{l["name"]}">{l["name"]}</a>'
            else:
                raise Exception(f"navbar_link type of {l['type']} is unknown. Known types: external (for internal links just remove the type keyvalue pair)")

        # internal links
        if not el:
            if pb.gc("toggles/slugify_html_links"):
                link = slugify_path(link)
            el = f'<a class="navbar-link" href="{html_url_prefix}/{link}" title="{l["name"]}">{l["name"]}</a>'

        elements.append(el)

    pb.navbar_links = elements
    return elements


def create_folder_navigation_view(pb) -> T.WriteExportFile:
    """This function creates the directory view file that is used as a base for the folder navigation view"""

    if not pb.gc("toggles/features/create_index_from_dir_structure/enabled"):
        return

    rel_output_path = pb.gc("toggles/features/create_index_from_dir_structure/rel_output_path")
    op = pb.paths["html_output_folder"].joinpath(rel_output_path)

    if verbose_enough("info", pb.verbosity):
        print(f"\t> COMPILING INDEX FROM DIR STRUCTURE ({op})")
    # Create dirtree to be viewed on its own
    if pb.gc("toggles/relative_path_html", cached=True):
        html_url_prefix = pb.sc(path="html_url_prefix", value=get_rel_html_url_prefix(pb.gc("toggles/features/create_index_from_dir_structure/rel_output_path")))
        print(html_url_prefix)
    pb.EnsureTreeObj()
    pb.treeobj.rel_output_path = pb.gc("toggles/features/create_index_from_dir_structure/rel_output_path")
    pb.treeobj.html_url_prefix = pb.gc("html_url_prefix")
    pb.treeobj.html = pb.treeobj.BuildIndex()
    pb.treeobj.WriteIndex()

    # Create dirtree to be included in every page
    if pb.gc("toggles/relative_path_html", cached=True):
        html_url_prefix = pb.sc(path="html_url_prefix", value="")
    pb.EnsureTreeObj()
    pb.treeobj.rel_output_path = "obs.html/dirtree.html"
    pb.treeobj.html_url_prefix = pb.gc("html_url_prefix")
    pb.treeobj.html = pb.treeobj.BuildIndex()
    pb.treeobj.WriteIndex()

    if verbose_enough("info", pb.verbosity):
        print("\t< COMPILING INDEX FROM DIR STRUCTURE: Done")


def recurseTagList(tagtree, tagpath, pb, level):
    """This function creates the folder `tags` in the html_output_folder, and a filestructure in that so you can navigate the tags."""

    # Get relevant paths
    # ---------------------------------------------------------
    tags_folder = pb.paths["html_output_folder"].joinpath("obs.html/tags/")

    tag_dst_path = tags_folder.joinpath(f"{tagpath}index.html").resolve()
    tag_dst_path_posix = tag_dst_path.as_posix()
    rel_dst_path_as_posix = tag_dst_path.relative_to(pb.paths["html_output_folder"]).as_posix()

    html_url_prefix = pb.gc("html_url_prefix")
    if pb.gc("toggles/relative_path_html", cached=True):
        html_url_prefix = pb.sc(path="html_url_prefix", value=get_rel_html_url_prefix(rel_dst_path_as_posix))

    # Make root dir
    tags_folder.mkdir(parents=True, exist_ok=True)

    # Compile markdown from tagtree
    # ---------------------------------------------------------
    md = f"\n# {tagpath[:-1]}\n"

    # Handle subtags
    if len(tagtree["subtags"].keys()) > 0:
        if level == 0:
            md += "## Tags\n"
        else:
            md += "## Subtags\n"

        for key in tagtree["subtags"].keys():
            # Point of recursion
            rel_key_path_as_posix = recurseTagList(tagtree["subtags"][key], tagpath + key + "/", pb, level + 1)
            md += f"- [{key}]({html_url_prefix}/{rel_key_path_as_posix})" + "\n"

    # Handle notes
    if len(tagtree["notes"]) > 0:
        md += "\n## Notes\n"
        for note_tuple in tagtree["notes"]:
            fo, url = note_tuple
            note_name = fo.md.GetNodeName()  # note_url.split('/')[-1].replace(".html", "")
            md += f"- [{note_name}]({html_url_prefix}/{url})\n"

    md += f"\n> [View all tags]({html_url_prefix}/obs.html/tags/index.html)"

    # Compile html
    extension_configs = {"codehilite": {"linenums": False}, "pymdownx.arithmatex": {"generic": True}}

    html_body = markdown.markdown(md, extensions=["extra", "codehilite", "obs_toc", "mermaid", "callout", "pymdownx.arithmatex"], extension_configs=extension_configs)

    di = '<link rel="stylesheet" href="' + html_url_prefix + '/obs.html/static/taglist.css" />'

    html = PopulateTemplate(
        pb,
        "none",
        pb.dynamic_inclusions,
        pb.html_template,
        html_url_prefix=html_url_prefix,
        content=html_body,
        dynamic_includes=di,
        container_wrapper_class_list=["single_tab_page-left-aligned"],
    )

    html = html.replace("{pinnedNode}", "tagspage")
    html = html.replace("{{navbar_links}}", "\n".join(pb.navbar_links))
    html = html.replace("{left_pane}", "").replace("{right_pane}", "")

    # Write file
    tag_dst_path.parent.mkdir(parents=True, exist_ok=True)
    with open(tag_dst_path_posix, "w", encoding="utf-8") as f:
        f.write(html)

    # Return link of this page, to be used by caller for building its page
    return rel_dst_path_as_posix


@cache
def create_foldable_tag_lists_html(pb, strip_tags=None):
    # strip_tags set
    strip_tags = expect_list(strip_tags)

    def rec_tag_tree_foldable(tag_tree, name, id, path="", strip_tags=None):
        subid = 0

        notes = ""
        if tag_tree["notes"]:
            notes += '<div class="tags-notes" style="font-weight:normal;"><ul class="tag-list">'
            tag_tree["notes"] = sorted(tag_tree["notes"], key=lambda x: x[1])  # sort on url #tag_tree['notes'].sort() #
            for note in tag_tree["notes"]:
                fo, url = note
                note_name = fo.md.GetNodeName()  # note.split('/')[-1].replace(".html", "")
                ahref = f'<a href="{pb.gc("html_url_prefix")}/{url}">{note_name}</a>'
                notes += f"<li>{ahref}</li>"
            notes += "</ul></div>"

        subtags = ""
        subtags_keys = list(tag_tree["subtags"].keys())
        subtags_keys.sort()

        for key in subtags_keys:
            # filter
            full_path = "/".join(list(filter(None, [path, name, key])))
            if full_path in strip_tags:
                continue

            # get subtags
            subtags += rec_tag_tree_foldable(
                tag_tree=tag_tree["subtags"][key],
                name=key,
                id=(str(id) + str(subid)),
                path="/".join(list(filter(None, [path, name]))),
                strip_tags=strip_tags,
            )
            subid += 1

        header = ""
        contents = f"{subtags}{notes}"
        if name:
            if path:
                path += "/"
            header = f'<button class="dir-button" onclick="toggle_id(\'{id}\')"><span class="tag-path">{path} </span>{name.capitalize()}</button>'
            contents = f'<div class="dir-container" id="{id}" style="font-weight:normal;">{contents}</div>'

        html = f'<div class="subtags">{header}{contents}</div>'
        return html

    # compile html
    html = rec_tag_tree_foldable(tag_tree=pb.tagtree, name="", id="tags-", strip_tags=strip_tags)
    return html


def create_foldable_tag_lists(pb):
    """Appends the output of recurseTagList by changing the tags/index.html to a dropdown page"""

    # set output path
    tags_folder = pb.paths["html_output_folder"].joinpath("obs.html/tags/")
    tag_dst_path = tags_folder.joinpath("index.html")
    tag_dst_path_posix = tag_dst_path.as_posix()
    tag_dst_path.parent.mkdir(parents=True, exist_ok=True)

    rel_dst_path_as_posix = tag_dst_path.relative_to(pb.paths["html_output_folder"]).as_posix()

    # set html_url_prefix
    html_url_prefix = pb.gc("html_url_prefix")
    if pb.gc("toggles/relative_path_html", cached=True):
        html_url_prefix = pb.sc(path="html_url_prefix", value=get_rel_html_url_prefix(rel_dst_path_as_posix))

    # compile html
    html = create_foldable_tag_lists_html(pb)
    html = PopulateTemplate(
        pb,
        "none",
        pb.dynamic_inclusions,
        pb.html_template,
        html_url_prefix=html_url_prefix,
        content=html,
        container_wrapper_class_list=["single_tab_page-left-aligned"],
    )
    html = html.replace("{pinnedNode}", "tagspage")
    html = html.replace("{{navbar_links}}", "\n".join(pb.navbar_links))
    html = html.replace("{left_pane}", "").replace("{right_pane}", "")

    # write to destination
    with open(tag_dst_path_posix, "w", encoding="utf-8") as f:
        f.write(html)
