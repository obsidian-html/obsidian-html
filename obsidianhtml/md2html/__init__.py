import regex as re
import urllib.parse  # convert link characters like %
import warnings

from .. import md2html

from ..features.SidePane import get_side_pane_id_by_content_selector
from ..features.add_toc_when_missing import gc_add_toc_when_missing, add_toc_when_missing

from ..parser.HeaderTree import convert_markdown_to_header_tree
from ..parser.MarkdownLink import MarkdownLink

from ..core.FileObject import FileObject
from ..lib import simpleHash, get_rel_html_url_prefix

from ..compiler.Templating import PopulateTemplate


def convert_markdown_page_to_html_and_export(fo: "FileObject", pb, backlink_node=None, log_level=1, capture_in_jar=False):
    """
    Takes a file object, opens the markdown file, edits the contents to prepare for conversion to html, copies images and other resources over to the
    output location, converts the md to html, writes the html content to the output directory, returns all the links to other markdown pages found
    in the page.
    """

    # Unpack picknick basket so we don't have to type too much.
    paths = pb.paths  # Paths of interest, such as the output and input folders
    files = pb.index.files  # Hashtable of all files found in the obsidian vault

    # Don't parse if not parsable
    if not fo.metadata["is_parsable_note"]:
        return ([], [])

    page_path = fo.path["markdown"]["file_absolute_path"]
    rel_dst_path = fo.path["html"]["file_relative_path"]

    if pb.gc("toggles/relative_path_html", cached=True):
        html_url_prefix = pb.sc(path="html_url_prefix", value=get_rel_html_url_prefix(rel_dst_path.as_posix()))
    else:
        html_url_prefix = pb.gc("html_url_prefix")

    page_depth = len(rel_dst_path.as_posix().split("/")) - 1

    # Load contents
    # ------------------------------------------------------------------
    # Create an object that handles a lot of the logic of parsing the page paths, content, etc
    md = fo.load_markdown_page("markdown")

    # Graph view integrations
    # ------------------------------------------------------------------
    # The nodelist will result in graph.json, which may have uses beyond the graph view

    # [17] Add self to nodelist
    node = pb.index.network_tree.add_file_object_to_node_list(fo, backlink_node)
    backlink_node = node

    # [425] Add included references as links in graph view
    if pb.gc("toggles/features/graph/show_inclusions_in_graph"):
        if "obs.html.data" in md.metadata and "inclusion_references" in md.metadata["obs.html.data"]:
            for incl in md.metadata["obs.html.data"]["inclusion_references"]:
                inc_md = files[incl].load_markdown_page("markdown")
                pb.index.network_tree.add_file_object_to_node_list(files[incl], backlink_node, link_type="inclusion")
                md.links.append(inc_md.fo)

    # Skip further processing if processing has happened already for this file
    # ------------------------------------------------------------------
    if fo.processed_mth is True:
        return ([], [])

    # Set file to processed
    fo.processed_mth = True

    if pb.gc("toggles/verbose_printout", cached=True):
        print("\t" * log_level, f"html: converting {page_path.as_posix()}")

    # Add page to search file
    # ------------------------------------------------------------------
    if pb.gc("toggles/features/search/enabled", cached=True):
        pb.search.AddPage(filename=page_path.stem, content=md.page, metadata=md.metadata, url=node["url"], rtr_url=node["rtr_url"], title=node["name"])

    # [1] Replace code blocks with placeholders so they aren't altered
    # They will be restored at the end
    # ------------------------------------------------------------------
    md.StripCodeSections()

    # Get all local markdown links.
    # ------------------------------------------------------------------
    # This is any string in between '](' and  ')' with no spaces in between the ( and )
    proper_links = re.findall(r"(?<=\]\()[^\s\]]+?(?=\))", md.page)
    for l in proper_links:
        ol = l

        l = urllib.parse.unquote(l)

        # There is currently no way to match links containing parentheses, AND not matching the last ) in a link like ([test](link))
        if l.endswith(")"):
            l = l[:-1]

        # Init link
        link = MarkdownLink(pb, l, page_path, paths["md_folder"])

        # Download buttons
        parts = l.split("|")
        if len(parts) > 1 and parts[-1] == "_obsidian_html_download_button_":
            link_name = parts[0]
            if link.fo is None:
                new_link = f"> **obsidian-html error:** Error creating download button for link {link_name}."
            else:
                link.fo.copy_file("mth")
                link_url = urllib.parse.quote(link.fo.get_link("html", origin=fo, encode_special=False))

                pb.search.AddFile(pb.gc, link.fo)

                new_link = f'<a class="download-button" target="_blank" download="" href="{link_url}"><span class="file-embed-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="svg-icon lucide-file"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline></svg></span>{link_name}</a>'

            safe_link = "\[[^\]]+?\]\(" + re.escape(ol) + "\)"
            md.page = re.sub(safe_link, new_link, md.page)
            continue

        # Don't process in the following cases (link empty or // in the link)
        if link.isValid is False or link.isExternal is True:
            continue

        # [12] Copy non md files over wholesale, then we're done for that kind of file
        if link.fo is None:
            if link.suffix != ".md" and "/obs.html/dir_index.html" not in link.url:
                path_key = "note"
                if not pb.gc("toggles/compile_md", cached=True):
                    path_key = "markdown"
                if pb.gc("toggles/warn_on_skipped_file", cached=True):
                    print(
                        "\t" * (log_level + 1),
                        "File " + str(link.url) + " not located, so not copied. @ " + pb.state["current_fo"].path[path_key]["file_absolute_path"].as_posix(),
                    )
        elif not link.fo.metadata["is_note"]:
            link.fo.copy_file("mth")
            pb.search.AddFile(pb.gc, link.fo)

        # [13] Link to a custom 404 page when linked to a not-created note
        if link.name == "not_created.md":
            new_link = f"]({html_url_prefix}/not_created.html)"
        else:
            if link.fo is None:
                continue

            md.links.append(link.fo)

            # [11.1] Rewrite .md links to .html (when the link is to a file in our root folder)
            query_part = ""
            if link.query != "":
                query_part = link.query_delimiter + link.query
            new_link = f']({urllib.parse.quote(link.fo.get_link("html", origin=fo, encode_special=False))}{query_part})'

        # Update link
        safe_link = re.escape("](" + ol + ")")
        md.page = re.sub(safe_link, new_link, md.page)

    # [?] Handle local source tag-links (copy them over to output)
    # ------------------------------------------------------------------
    for link in re.findall(r'(?<=<source src=")([^"]*)', md.page):
        l = urllib.parse.unquote(link)
        if "://" in l:
            continue

        rel_path_str, lo = pb.FileFinder.FindFile(l, pb)
        if rel_path_str is False:
            if pb.gc("toggles/warn_on_skipped_image", cached=True):
                warnings.warn(f"Media {l} treated as external and not imported in html")
            continue

        # Copy src to dst
        lo.copy_file("mth")
        pb.search.AddFile(pb.gc, lo)

        # [11.2] Adjust video link in page to new dst folder (when the link is to a file in our root folder)
        new_link = '<source src="' + urllib.parse.quote(lo.get_link("html", origin=fo, encode_special=False)) + '"'
        safe_link = r'<source src="' + re.escape(link) + r'"'
        md.page = re.sub(safe_link, new_link, md.page)

    # [?] Handle local img tag-links (copy them over to output)
    # ------------------------------------------------------------------
    for tag in re.findall(r'<img src=".*?>', md.page):
        # get template and link from tag
        # e.g. <img src="200w.gif"  width="200"> --> <img src="{link}"  width="200"> & 200w.gif
        parts = tag.split('src="')
        iparts = parts[1].split('"', 1)
        link = iparts[0]
        template = parts[0] + 'src="{link}"'
        if len(iparts) > 1:
            template = template + iparts[1]

        l = urllib.parse.unquote(link)
        if "://" in l:
            continue

        rel_path_str, lo = pb.FileFinder.FindFile(l, pb)
        if rel_path_str is False:
            if pb.gc("toggles/warn_on_skipped_image", cached=True):
                warnings.warn(f"Media {l} treated as external and not imported in html")
            continue

        # Copy src to dst
        if lo.path["markdown"]["file_absolute_path"].exists():
            lo.copy_file("mth")

            pb.search.AddFile(pb.gc, lo)

        # [11.2] Adjust video link in page to new dst folder (when the link is to a file in our root folder)
        new_link = template.replace("{link}", urllib.parse.quote(lo.get_link("html", origin=fo, encode_special=False)))
        safe_link = re.escape(tag)
        md.page = re.sub(safe_link, new_link, md.page)

    # [?] Handle local embeddable tag-links (copy them over to output)
    # ------------------------------------------------------------------
    for link in re.findall(r'(?<=<embed src=")([^"]*)', md.page):
        l = urllib.parse.unquote(link)
        if "://" in l:
            continue

        rel_path_str, lo = pb.FileFinder.FindFile(l, pb)
        if rel_path_str is False:
            if pb.gc("toggles/warn_on_skipped_image", cached=True):
                warnings.warn(f"Media {l} treated as external and not imported in html")
            continue

        # Copy src to dst
        lo.copy_file("mth")
        pb.search.AddFile(pb.gc, lo)

        # [11.2] Adjust video link in page to new dst folder (when the link is to a file in our root folder)
        new_link = '<embed src="' + urllib.parse.quote(lo.get_link("html", origin=fo, encode_special=False)) + '"'
        safe_link = r'<embed src="' + re.escape(link) + r'"'
        md.page = re.sub(safe_link, new_link, md.page)

    # [?] Documentation styling: Table of Contents
    # ------------------------------------------------------------------
    if get_side_pane_id_by_content_selector(pb, "toc") or gc_add_toc_when_missing(pb, fo):
        # convert the common [[_TOC_]] into [TOC]
        md.page = md.page.replace("[[_TOC_]]", "[TOC]")

    if gc_add_toc_when_missing(pb, fo):
        md.page = add_toc_when_missing(pb, md.page, md.metadata)

    # -- [8] Insert markdown links for bare http(s) links (those without the [name](link) format).
    # Cannot start with [, (, nor "
    # match 'http://* ' or 'https://* ' (end match by whitespace)
    # Note that note->md step also does this, this should be void if doing note-->html, but useful when doing md->html
    for l in re.findall('(?<![\[\("])(https*:\/\/.[^\s]*)', md.page):
        new_md_link = f"[{l}]({l})"
        safe_link = re.escape(l)
        md.page = re.sub(f"(?<![\[\(])({safe_link})", new_md_link, md.page)

    # strip svg, as python-markdown corrupts these
    # ------------------------------------------------------------------
    svgs = md.strip_svgs()

    # [1] Restore codeblocks/-lines
    # ------------------------------------------------------------------
    md.RestoreCodeSections()

    # [11] Convert markdown to html
    # ------------------------------------------------------------------
    html_body = md2html.pythonmarkdown_convert_md_to_html(pb, md.page, rel_dst_path)
    html_body = f'<div class="content">{html_body}</div>'

    # restore svg, as python-markdown corrupts these
    # ------------------------------------------------------------------
    for i, v in enumerate(svgs):
        html_body = html_body.replace("---obsidian_html_svg_block_" + str(i), v)

    if capture_in_jar:
        pb.jars[capture_in_jar] = html_body

    # HTML Tweaks
    # [??] Embedded note titles integration
    # ------------------------------------------------------------------
    # if pb.capabilities_needed["embedded_note_titles"]:
    #     if "obs.html.tags" in fo.md.metadata.keys() and "dont_add_embedded_title" in fo.md.metadata["obs.html.tags"]:
    #         pass
    #     else:
    #         title = node["name"]

    #         # overwrite node name (titleMetadataField)
    #         if "titleMetadataField" in pb.plugin_settings["embedded_note_titles"].keys():
    #             title_key = pb.plugin_settings["embedded_note_titles"]["titleMetadataField"]
    #             if title_key in node["metadata"].keys():
    #                 title = node["metadata"][title_key]

    #         # hide if h1 is present
    #         hide = False
    #         if pb.gc("toggles/features/embedded_note_titles/hide_on_h1"):
    #             header_dict, root_element = convert_markdown_to_header_tree(md.page)
    #             if (
    #                 len(root_element["content"]) > 0
    #                 and isinstance(root_element["content"][0], dict)
    #                 and root_element["content"][0]["level"] == 1
    #             ):
    #                 hide = True

    #         # hideOnMetadataField
    #         if (
    #             "hideOnMetadataField" in pb.plugin_settings["embedded_note_titles"].keys()
    #             and pb.plugin_settings["embedded_note_titles"]["hideOnMetadataField"]
    #         ):
    #             if "embedded-title" in node["metadata"].keys() and node["metadata"]["embedded-title"] is False:
    #                 hide = True

    #         # add embedded title
    #         if not hide:
    #             html_body = f"<embeddedtitle>{title}</embeddedtitle>\n" + html_body

    # ------------------------------------------------------------------
    # [14] Tag external/anchor links with a class so they can be decorated differently
    for l in re.findall(r'(?<=\<a href=")([^"]*)', html_body):
        if l == "":
            continue

        # anchor links
        if l[0] == "#":
            new_str = f'<a href="{l}" class="anchor-link"'

        # not internal or internal and not .html file
        elif (l[0] not in ("/", ".")) or ("." in l.split("/")[-1] and ".html" not in l.split("/")[-1]):
            # add in target="_blank" (or not)
            external_blank_html = ""
            if pb.gc("toggles/external_blank", cached=True):
                external_blank_html = 'target="_blank" '

            new_str = f'<a href="{l}" {external_blank_html}class="external-link"'
        else:
            continue

        # convert link
        safe_str = f'<a href="{l}"'
        html_body = html_body.replace(safe_str, new_str)

    # [15] Tag not created links with a class so they can be decorated differently
    html_body = html_body.replace(f'<a href="{html_url_prefix}/not_created.html">', f'<a href="{html_url_prefix}/not_created.html" class="nonexistent-link">')

    html_body += '\n<div class="note-footer">\n'

    # [??] breadcrumbs
    if pb.gc("toggles/features/breadcrumbs/enabled", cached=True):
        html_body = "{_obsidian_html_breadcrumbs_pattern_}\n" + html_body

    # [18] add backlinks to page
    if pb.gc("toggles/features/backlinks/enabled", cached=True):
        html_body += "{_obsidian_html_backlinks_pattern_}\n"

    # [18] add tags to page
    if pb.gc("toggles/features/tags_page/styling/show_in_note_footer", cached=True):
        html_body += '<div class="tags">\n{_obsidian_html_tags_footer_pattern_}\n</div>\n'

    html_body += "\n</div>"  # class="note-footer"

    # [17] Add in graph code to template (via {content})
    # This shows the "Show Graph" button, and adds the js code to handle showing the graph
    if pb.gc("toggles/features/graph/enabled", cached=True):
        graph_template = (
            pb.graph_template.replace("{id}", simpleHash(html_body))
            .replace("{pinnedNode}", node["id"])
            .replace("{pinnedNodeGraph}", str(node["nid"]))
            .replace("{html_url_prefix}", html_url_prefix)
            .replace("{graph_coalesce_force}", pb.gc("toggles/features/graph/coalesce_force", cached=True))
            .replace("{graph_classes}", "")
        )
        html_body += f"\n{graph_template}\n"

    # Add node_id to page so that we can fetch this in the second-pass
    html_body += "{_obsidian_html_node_id_pattern_:" + node["id"] + "}\n"

    # [16] Wrap body html in valid html structure from template
    # ------------------------------------------------------------------
    html = PopulateTemplate(pb, node["id"], pb.dynamic_inclusions, pb.html_template, content=html_body)

    html = html.replace("{node_name}", node["name"])
    html = html.replace("{pinnedNode}", node["id"]).replace("{html_url_prefix}", html_url_prefix).replace("{page_depth}", str(page_depth))
    # [?] Documentation styling: Navbar
    # ------------------------------------------------------------------
    html = html.replace("{{navbar_links}}", "\n".join(pb.navbar_links))

    # Save file
    # ------------------------------------------------------------------
    fo.path["html"]["file_absolute_path"].parent.mkdir(parents=True, exist_ok=True)
    html_dst_path_posix = fo.path["html"]["file_absolute_path"].as_posix()

    md.AddToTagtree(pb.tagtree, fo.path["html"]["file_relative_path"].as_posix())

    # Write html
    with open(html_dst_path_posix, "w", encoding="utf-8") as f:
        f.write(html)

    # Return links to crawl through linked notes
    # ------------------------------------------------------------------
    return (backlink_node, md.links)


def pythonmarkdown_convert_md_to_html(pb, page, rel_dst_path):
    import markdown
    from ..markdown_extensions.CallOutExtension import CallOutExtension

    # from ..markdown_extensions.DataviewExtension import DataviewExtension
    from ..markdown_extensions.MermaidExtension import MermaidExtension
    from ..markdown_extensions.CustomTocExtension import CustomTocExtension
    from ..markdown_extensions.EraserExtension import EraserExtension
    from ..markdown_extensions.FootnoteExtension import FootnoteExtension
    from ..markdown_extensions.FormattingExtension import FormattingExtension
    from ..markdown_extensions.EmbeddedSearchExtension import EmbeddedSearchExtension
    from ..markdown_extensions.CodeWrapperExtension import CodeWrapperExtension
    from ..markdown_extensions.AdmonitionExtension import AdmonitionExtension
    from ..markdown_extensions.BlockLinkExtension import BlockLinkExtension

    extensions = [
        "abbr",
        "attr_list",
        "def_list",
        "fenced_code",
        "tables",
        "md_in_html",
        FormattingExtension(),
        "codehilite",
        CustomTocExtension(),
        CallOutExtension(),
        "pymdownx.arithmatex",
    ]

    extension_configs = {"codehilite": {"linenums": False}, "pymdownx.arithmatex": {"generic": True}}

    if pb.gc("toggles/features/footnote_md_extension/enabled"):
        extensions.append(FootnoteExtension())

    if pb.gc("toggles/features/mermaid_diagrams/enabled"):
        strip_special_chars = pb.gc("toggles/features/mermaid_diagrams/strip_special_chars")
        extensions.append(MermaidExtension(strip_special_chars=strip_special_chars))

    if pb.gc("toggles/features/dataview/enabled"):
        extensions.append("dataview")
        extension_configs["dataview"] = {"note_path": rel_dst_path, "dataview_export_folder": pb.paths["dataview_export_folder"]}

    if pb.gc("toggles/features/eraser/enabled"):
        extensions.append(EraserExtension())

    if pb.gc("toggles/features/embedded_search/enabled"):
        extensions.append(EmbeddedSearchExtension())

    extensions.append(CodeWrapperExtension())
    extensions.append(AdmonitionExtension())
    extensions.append(BlockLinkExtension())

    html_body = markdown.markdown(page, extensions=extensions, extension_configs=extension_configs)
    return html_body


def insert_backlinks(pb, html, node_id, page_depth):
    backlinks = [x for x in pb.index.network_tree.tree["links"] if x["target"] == node_id]
    snippet = ""
    if len(backlinks) > 0:
        snippet = "<h2>Backlinks</h2>\n<ul>\n"
        for l in backlinks:
            if l["target"] == node_id:
                url = pb.index.network_tree.node_lookup[l["source"]]["url"]
                if pb.gc("toggles/relative_path_html", cached=True):
                    url = ("../" * page_depth) + pb.index.network_tree.node_lookup[l["source"]]["rtr_url"]
                if url[0] not in [".", "/"]:
                    url = "/" + url
                snippet += f'\t<li><a class="backlink" href="{url}">{l["source"]}</a></li>\n'
        snippet += "</ul>"
        snippet = f'<div class="backlinks">\n{snippet}\n</div>\n'
    else:
        snippet = '<div class="backlinks" style="display:none"></div>\n'

    # replace placeholder with list & write output
    return re.sub("\{_obsidian_html_backlinks_pattern_\}", snippet, html)


def get_tags(node):
    if "tags" in node["metadata"] and len(node["metadata"]["tags"]) > 0:
        return node["metadata"]["tags"]
    return []


def insert_tags_footer(pb, html, tags, md_metadata):
    # remove placeholder
    if bool(tags) is False or ("obs.html.tags" in md_metadata.keys() and "no_tag_footer" in md_metadata["obs.html.tags"]):
        return re.sub(r"\{_obsidian_html_tags_footer_pattern_\}", "", html)

    snippet = "<h2>Tags</h2>\n<ul>\n"
    for tag in tags:
        url = f'{pb.gc("html_url_prefix")}/obs.html/tags/{tag}/index.html'
        snippet += f'\t<li><a class="backlink" href="{url}">{tag}</a></li>\n'

        if pb.gc("toggles/preserve_inline_tags", cached=True):
            placeholder = re.escape("<code>{_obsidian_pattern_tag_" + tag + "}</code>")
            inline_tag = f'<a class="inline-tag" href="{url}">{tag}</a>'
            html = re.sub(placeholder, inline_tag, html)
    snippet += "</ul>"

    # replace placeholder with list & write output
    return re.sub(r"\{_obsidian_html_tags_footer_pattern_\}", snippet, html)
