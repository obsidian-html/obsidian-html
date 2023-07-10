import sys
import frontmatter
import gzip
import yaml

import regex as re  # regex string finding/replacing

from urllib.parse import unquote
from pathlib import Path

from .. import md2html

from ..lib import CreateStaticFilesFolders, WriteFileLog, simpleHash, get_html_url_prefix, retain_reference, OpenIncludedFile, slugify

from ..compiler.Templating import PopulateTemplate
from ..core.PicknickBasket import PicknickBasket
from ..core.FileObject import FileObject
from ..core.Index import Index

from ..features.RssFeed import RssFeed
from ..features.CreateIndexFromTags import CreateIndexFromTags
from ..features.EmbeddedSearch import EmbeddedSearch
from ..features.SidePane import get_side_pane_html
from ..features import post_processing

from ..compiler.HTML import compile_navbar_links, create_folder_navigation_view, create_foldable_tag_lists, recurseTagList
from ..compiler.Templating import ExportStaticFiles

from ..modules import controller as module_controller
from ..modules.lib import verbose_enough


def ConvertVault(config_yaml_location=""):
    # Set config
    # ---------------------------------------------------------
    pb = PicknickBasket()

    # Bootstrap module system
    # ----------------------------------------------------------
    module_result, setup_module = module_controller.run_module_setup(pb=pb)
    module_data_folder = module_result.output
    config_file_path = module_data_folder + "/config.yml"
    with open(config_file_path, "r") as f:
        cfg = yaml.safe_load(f.read())
        verbosity = cfg["verbosity"]

    # The first module will always have to be run, and we need info back, so this is a bit of a weird one as far as modules are concerned
    module_list, meta_modules_post = module_controller.load_module_itenary(module_data_folder)
    instantiated_modules = {}

    # compile list of which module provides/requires which modfile
    all_module_listings = module_list.copy()
    all_module_listings["meta_modules"] = meta_modules_post
    setup_module.compile_modfile_lookups(all_module_listings)

    # Run modules
    # ----------------------------------------------------------
    defaults = {
        "module_data_folder": module_data_folder,
        "verbosity": verbosity,
        "meta_modules_post": meta_modules_post,
        "instantiated_modules": instantiated_modules,
        "pb": pb,
    }

    def run_module(m):
        module_controller.run_module(
            module_name=m["name"], method=m["method"], persistent=m["persistent"], module_source=m["file"], module_binary=m["binary"], module_class_name=m["module_class"], **defaults
        )

    for module_listing in module_list["preparation"]:
        run_module(module_listing)
    # for module_listing in module_list["indexing"]:
    #     run_module(module_listing)
    for module_listing in module_list["finalize"]:
        run_module(module_listing)

    # Load input files into file tree
    # ---------------------------------------------------------
    Index(pb)

    # Convert
    # ---------------------------------------------------------
    convert_obsidian_notes_to_markdown(pb)
    convert_markdown_to_html(pb)
    compile_rss_feed(pb)
    export_user_files(pb)
    run_post_processing(pb)

    # Wrap up
    # ---------------------------------------------------------
    if pb.gc("toggles/compile_md") or pb.gc("toggles/compile_html"):
        if verbose_enough("info", pb.verbosity):
            print("\nYou can find your output at:")
            if pb.gc("toggles/compile_md"):
                print(f"\tmd: {pb.paths['md_folder']}")
            if pb.gc("toggles/compile_html"):
                print(f"\thtml: {pb.paths['html_output_folder']}")


def convert_obsidian_notes_to_markdown(pb):
    if pb.gc("toggles/compile_md", cached=True):
        # Create index.md based on given tagnames, that will serve as the entrypoint
        # ---------------------------------------------------------
        if pb.gc("toggles/features/create_index_from_tags/enabled"):
            CreateIndexFromTags(pb)

        # Start conversion with entrypoint.
        # ---------------------------------------------------------
        # Note: this will mean that any note not (indirectly) linked by the entrypoint will not be included in the output!

        if verbose_enough("info", pb.verbosity):
            print(f'> COMPILING MARKDOWN FROM OBSIDIAN CODE ({str(pb.paths["obsidian_entrypoint"])})')

        if pb.gc("toggles/debug_filetree_keys"):
            for k, v in pb.index.files.items():
                print(k)

        # Force search to lowercase
        rel_entry_path_str = pb.paths["rel_obsidian_entrypoint"].as_posix()
        if pb.gc("toggles/force_filename_to_lowercase", cached=True):
            rel_entry_path_str = rel_entry_path_str.lower()

        # Start conversion
        entrypoint_file_object = pb.index.files[rel_entry_path_str]
        pb.init_state(action="n2m", loop_type="note", current_fo=entrypoint_file_object, subroutine="crawl_obsidian_notes_and_convert_to_markdown")
        crawl_obsidian_notes_and_convert_to_markdown(entrypoint_file_object, pb)
        pb.reset_state()

        # also do the tags page if it is not the index, otherwise this page will never be hit
        if pb.gc("toggles/features/create_index_from_tags/enabled") and not pb.gc("toggles/features/create_index_from_tags/use_as_homepage"):
            entrypoint_file_object = pb.index.files[pb.gc("toggles/features/create_index_from_tags/rel_output_path")]
            pb.init_state(action="n2m", loop_type="note", current_fo=entrypoint_file_object, subroutine="crawl_obsidian_notes_and_convert_to_markdown")
            crawl_obsidian_notes_and_convert_to_markdown(entrypoint_file_object, pb)
            pb.reset_state()

        # Keep going until all other files are processed
        if pb.gc("toggles/process_all", cached=True):
            if verbose_enough("info", pb.verbosity):
                print("\t> FEATURE: PROCESS ALL")
            unparsed = [x for x in pb.index.files.values() if x.processed_ntm is False]
            i = 0
            l = len(unparsed)
            for fo in unparsed:
                i += 1
                if pb.gc("toggles/verbose_printout", cached=True) is True:
                    print(f"\t\t{i}/{l} - " + str(fo.path["note"]["file_absolute_path"]))
                pb.init_state(action="n2m_process_all", loop_type="note", current_fo=fo, subroutine="crawl_obsidian_notes_and_convert_to_markdown")
                crawl_obsidian_notes_and_convert_to_markdown(fo, pb, log_level=2)
                pb.reset_state()
            if verbose_enough("info", pb.verbosity):
                print("\t< FEATURE: PROCESS ALL: Done")


def convert_markdown_to_html(pb):
    if not pb.gc("toggles/compile_html", cached=True):
        return

    if verbose_enough("info", pb.verbosity):
        print(f'> COMPILING HTML FROM MARKDOWN CODE ({str(pb.paths["md_entrypoint"])})')

    # Prepare reusable blocks
    compile_navbar_links(pb)

    # Force search to lowercase
    rel_entry_path_str = pb.paths["rel_md_entrypoint_path"].as_posix()
    if pb.gc("toggles/force_filename_to_lowercase", cached=True):
        rel_entry_path_str = rel_entry_path_str.lower()


    # add in the not_created page
    # -----------------------------------------------------------
    rel_path="not_created.md"
    abs_path = pb.paths["md_folder"].joinpath(rel_path)
    contents = OpenIncludedFile("html/templates/not_created.md")
    with open(abs_path, 'w') as f:
        f.write(contents)

    fo = FileObject(pb)
    fo.init_markdown_path(abs_path)
    fo.compile_metadata(abs_path)
    pb.index.add_file_object_to_file_tree(rel_path, fo)
    pb.FileFinder.invalidate_cache()


    # Conversion: md -> html
    # -----------------------------------------------------------
    # Start conversion from the entrypoint
    entrypoint_file_object = pb.index.files[rel_entry_path_str]
    pb.init_state(action="m2h", loop_type="md_note", current_fo=entrypoint_file_object, subroutine="crawl_markdown_notes_and_convert_to_html")
    crawl_markdown_notes_and_convert_to_html(entrypoint_file_object, pb)
    pb.reset_state()

    # Run other pages that otherwise might not be hit
    ## tags page
    if pb.gc("toggles/features/create_index_from_tags/enabled") and not pb.gc("toggles/features/create_index_from_tags/use_as_homepage"):
        entrypoint_file_object = pb.index.files[pb.gc("toggles/features/create_index_from_tags/rel_output_path")]
        pb.init_state(action="m2h", loop_type="md_note", current_fo=entrypoint_file_object, subroutine="crawl_markdown_notes_and_convert_to_html")
        crawl_markdown_notes_and_convert_to_html(entrypoint_file_object, pb, capture_in_jar="tags_page_html")
        pb.reset_state()

    ## not_created
    entrypoint_file_object = pb.index.files["not_created.md"]
    crawl_markdown_notes_and_convert_to_html(fo, pb)

    # Keep going until all other files are processed
    if pb.gc("toggles/process_all") is True:
        if verbose_enough("info", pb.verbosity):
            print("\t> FEATURE: PROCESS ALL")
        unparsed = [x for x in pb.index.files.values() if x.processed_mth is False]
        i = 0
        l = len(unparsed)
        for fo in unparsed:
            i += 1
            if pb.gc("toggles/verbose_printout", cached=True) is True:
                print(f"\t\t{i}/{l} - " + str(fo.path["markdown"]["file_absolute_path"]))

            pb.init_state(action="m2h_process_all", loop_type="md_note", current_fo=fo, subroutine="crawl_markdown_notes_and_convert_to_html")
            crawl_markdown_notes_and_convert_to_html(fo, pb, log_level=2)
            pb.reset_state()

        if verbose_enough("info", pb.verbosity):
            print("\t< FEATURE: PROCESS ALL: Done")

    # [??] Second pass
    # ------------------------------------------
    # Some code can only be generated when all the notes have already been created.
    # These steps are done in this block.

    # Create reusable blocks
    create_folder_navigation_view(pb)

    # Make lookup so that we can easily find the url of a node
    pb.index.network_tree.compile_node_lookup()

    # Prep some data outside of the loop
    pb.index.compile_html_relpath_lookup_table()

    esearch = None
    if pb.gc("toggles/features/embedded_search/enabled", cached=True):
        esearch = EmbeddedSearch(json_data=pb.search.OutputJson())

    # prepare lookup to translate slugified folder names to their original
    folder_og_name_lut = {}
    for file in pb.index.files.keys():
        file_path = pb.index.files[file].path["markdown"]["file_relative_path"]
        for el in file_path.as_posix().split("/")[:-1]:
            slug_el = slugify(el)
            if slug_el not in folder_og_name_lut:
                folder_og_name_lut[slug_el] = el

    if verbose_enough("info", pb.verbosity):
        print("\t> SECOND PASS HTML")

    for fo in pb.index.files.values():
        if not fo.metadata["is_note"]:
            continue

        # get paths / html prefix
        dst_abs_path = fo.path["html"]["file_absolute_path"]
        dst_rel_path_str = fo.path["html"]["file_relative_path"].as_posix()
        html_url_prefix = get_html_url_prefix(pb, rel_path_str=dst_rel_path_str)
        page_depth = len(dst_rel_path_str.split("/")) - 1

        # get html content
        try:
            with open(dst_abs_path, "r", encoding="utf-8") as f:
                html = f.read()
        except:
            continue

        # Get node_id
        m = re.search(r"(?<=\{_obsidian_html_node_id_pattern_:)(.*?)(?=\})", html)
        if m is None:
            continue
        node_id = m.group(0)
        node = pb.index.network_tree.node_lookup[node_id]
        html = re.sub("\{_obsidian_html_node_id_pattern_:" + re.escape(node_id) + "}", "", html)

        # Get tags
        tags = md2html.get_tags(node)

        # Fill in side pane content
        left_pane = get_side_pane_html(pb, "left_pane", node)
        html = html.replace("{left_pane}", left_pane)

        right_pane = get_side_pane_html(pb, "right_pane", node)
        html = html.replace("{right_pane}", right_pane)

        # Compile backlinks list
        if pb.gc("toggles/features/backlinks/enabled", cached=True):
            html = md2html.insert_backlinks(pb, html, node_id, page_depth)

        # Insert tags footer
        html = md2html.insert_tags_footer(pb, html, tags, fo.md.metadata)

        # add breadcrumbs
        # ------------------------------------------------------------------------
        if pb.gc("toggles/features/breadcrumbs/enabled", cached=True):
            html_url_prefix = pb.gc("html_url_prefix", cached=True)

            if node["url"] == f"{html_url_prefix}/index.html":
                # Don't create breadcrumbs for the homepage
                snippet = ""

            else:
                # loop through all/links/along/the_way.html

                # set first element to be home
                parts = [f'<a href="{html_url_prefix}/" style="color: rgb(var(--normal-text-color));">Home</a>']

                subpaths = node["url"].replace(".html", "").split("/")[1:]

                if pb.gc("toggles/force_filename_to_lowercase", cached=True):
                    subpaths = [x.lower() for x in subpaths]

                if html_url_prefix:
                    # remove the parts that are part of the prefix
                    prefix_amount = len(html_url_prefix.split("/")) - 1
                    subpaths = subpaths[prefix_amount:]

                previous_url = ""
                for i, subpath in enumerate(subpaths):
                    subpath = unquote(subpath)
                    if subpath in pb.index.network_tree.node_lookup:
                        lnode = pb.index.network_tree.node_lookup[subpath]
                    elif subpath in pb.index.network_tree.node_lookup_slug:
                        lnode = pb.index.network_tree.node_lookup_slug[subpath]
                    else:
                        # try finding folder with same name in markdown folder
                        # to get proper capitalization, even if we use slugify
                        name = unquote(subpaths[i])
                        if name in folder_og_name_lut:
                            name = folder_og_name_lut[name]

                        parts.append(f'<span style="color: #666;">{name}</span>')
                        previous_url = ""
                        continue

                    url = lnode["url"]
                    name = lnode["name"]

                    # in the case of folder notes, we have the folder and note name being the
                    # same, we don't want to print this twice in the breadcrumbs
                    if url != previous_url:
                        parts.append(f'<a href="{url}" ___COLOR___>{name}</a>')
                    previous_url = url

                # set all links to be normal text color except for the last link
                parts[-1] = parts[-1].replace("___COLOR___", "")
                for i, link in enumerate(parts):
                    parts[i] = link.replace("___COLOR___", 'style="color: var(--normal-text-color);"')

                # combine parts into snippet
                snippet = " / ".join(parts)
                snippet = f"""
                <div style="width:100%; text-align: right;display: block;margin: 0.5rem;">
                    <div style="flex:1;display: none;"></div>
                    <div class="breadcrumbs" style="flex:1 ;padding: 0.5rem; width: fit-content;display: inline;border-radius: 0.2rem;">
                        {snippet}
                    </div>
                </div>"""

            html = re.sub("\{_obsidian_html_breadcrumbs_pattern_\}", snippet, html)

        # add embedded search results
        if pb.gc("toggles/features/embedded_search/enabled", cached=True):
            query_blocks = re.findall(r"(?<=<p>{_obsidian_html_query:)(.*?)(?=\ }</p>)", html)
            for listing in query_blocks:
                # split listing into qualifier and user_query
                qual, user_query = listing.split("|-|")

                # found query
                print(qual, user_query)

                # search
                res = esearch.search(user_query)

                # compile html output
                output = ""
                if qual == "list":
                    output = '<div class="query"><ul>\n\t' + "\n\t".join([f'<li><a href="/{x["path"]}">{x["title"]}</a></li>' for x in res]) + "\n</ul></div>"

                else:
                    output = '<div class="query">'
                    for doc in res:
                        # setup doc
                        output += f'\n\t<div class="match-document">\n\t\t<div class="match-document-title">\n\t\t\t<a href="/{doc["path"]}">{doc["title"]}</a>\n\t\t</div>\n\t\t<div class="matches">'

                        # Add path matches
                        if doc["matches"]["path"]:
                            output += '\n\t\t\t<div class="match-row">\n\t\t\t\t' + doc["matches"]["path"] + "\n\t\t\t</div>"

                        # Add content mathes
                        for match in doc["matches"]["content"]:
                            output += f'\n\t\t\t<div class="match-row">\n\t\t\t\t{match}\n\t\t\t</div>'

                        # Add tags
                        if len(doc["matches"]["tags"]) > 0:
                            output += '\n\t\t\t<div class="tag-box">'
                            for match, tag in doc["matches"]["tags"]:
                                output += f'\n\t\t\t\t<div class="match-row tag">\n\t\t\t\t\t<a href="/obs.html/tags/{tag}/index.html">{match}</a>\n\t\t\t\t</div>'
                            output += "\n\t\t\t</div>"

                        if len(doc["matches"]["tags_keyword"]) > 0:
                            output += '\n\t\t\t<div class="tag-box">'
                            for match, tag in doc["matches"]["tags_keyword"]:
                                output += f'\n\t\t\t\t<div class="match-row tag keyword">\n\t\t\t\t\t<a href="/obs.html/tags/{tag}/index.html">{match}</a>\n\t\t\t\t</div>'
                            output += "\n\t\t\t</div>"

                        # close doc divs
                        output += "\n\t\t</div>\n\t</div>"
                    # close query div
                    output += "\n</div>"

                # replace query block with html
                try:
                    safe_str = re.escape("<p>{_obsidian_html_query:" + listing + " }</p>")
                    html = re.sub(safe_str, output, html)
                except:
                    print(listing)
                    raise

        # write result
        with open(dst_abs_path, "w", encoding="utf-8") as f:
            f.write(html)

    if verbose_enough("info", pb.verbosity):
        print("\t< SECOND PASS HTML: Done")

    # Create system pages
    # -----------------------------------------------------------
    # Create tag pages
    recurseTagList(pb.tagtree, "", pb, level=0)
    create_foldable_tag_lists(pb)

    # Create graph fullpage
    if pb.gc("toggles/features/graph/enabled", cached=True):
        # compile graph
        html = PopulateTemplate(pb, "null", pb.dynamic_inclusions, pb.graph_full_page_template, content="")
        html = html.replace("{{navbar_links}}", "\n".join(pb.navbar_links)).replace("{page_depth}", "2")

        op = pb.paths["html_output_folder"].joinpath("obs.html/graph/index.html")
        op.parent.mkdir(parents=True, exist_ok=True)

        with open(op, "w", encoding="utf-8") as f:
            f.write(html)

    if pb.capabilities_needed["graph_data"]:
        # add crosslinks to graph data
        pb.index.network_tree.AddCrosslinks()

        # Write node json to static folder
        CreateStaticFilesFolders(pb.paths["html_output_folder"])
        with open(pb.paths["html_output_folder"].joinpath("obs.html").joinpath("data/graph.json"), "w", encoding="utf-8") as f:
            f.write(pb.index.network_tree.OutputJson())

    if pb.capabilities_needed["search_data"]:
        # Compress search json and write to static folder
        gzip_path = pb.paths["html_output_folder"].joinpath("obs.html").joinpath("data/search.json.gzip")
        gzip_path.parent.mkdir(parents=True, exist_ok=True)
        gzip_content = pb.search.OutputJson()
        # pb.gzip_hash = simpleHash(gzip_content.decode("utf-8"))
        pb.gzip_hash = simpleHash(gzip_content)

        with gzip.open(gzip_path, "wb", compresslevel=5) as f:
            # f.write(gzip_content)
            f.write(gzip_content.encode("utf-8"))

    # Add Extra stuff to the output directories
    ExportStaticFiles(pb)

    if verbose_enough("info", pb.verbosity):
        print("< COMPILING HTML FROM MARKDOWN CODE: Done")


def compile_rss_feed(pb):
    if not pb.gc("toggles/features/rss/enabled"):
        return

    if verbose_enough("info", pb.verbosity):
        print("> COMPILING RSS FEED")
    feed = RssFeed(pb)
    feed.Compile()
    if verbose_enough("info", pb.verbosity):
        print("< COMPILING RSS FEED: Done")


def export_user_files(pb):
    if not pb.gc("file_exports"):
        return
    file_exports = pb.gc("file_exports")
    if not isinstance(file_exports, list):
        raise Exception(f"Config value type of file_exports should be list, instead of {type(file_exports).__name__}.")

    if verbose_enough("info", pb.verbosity):
        print("> EXPORTING USER FILES")

    for ufile in file_exports:
        src = pb.paths["obsidian_folder"].joinpath(ufile["src"]).resolve()
        dst = pb.paths["html_output_folder"].joinpath(ufile["dst"]).resolve()
        if not src.exists():
            raise Exception(f"File {src.as_posix()} not found")
        if "encoding" not in ufile:
            encoding = "utf-8"
        else:
            encoding = ufile["encoding"]

        print(f"\tWriting {src.as_posix()} to {dst.as_posix()} ({encoding})")

        if encoding == "binary":
            with open(src, "rb") as f:
                contents = f.read()
            with open(dst, "wb") as f:
                f.write(contents)
        else:
            with open(src, "r", encoding=encoding) as f:
                contents = f.read()
            with open(dst, "w", encoding=encoding) as f:
                f.write(contents)

    if verbose_enough("info", pb.verbosity):
        print("< EXPORTING USER FILES: Done")


# @extra_info()
def crawl_obsidian_notes_and_convert_to_markdown(fo: "FileObject", pb, log_level=1, iteration=0):
    """This functions converts an obsidian note to a markdown file and calls itself on any local note links it finds in the page."""

    # Don't parse if not parsable
    if not fo.metadata["is_parsable_note"]:
        return

    if pb.gc("toggles/stdout_current_file", cached=True):
        print(fo.path["note"]["file_absolute_path"].as_posix().encode("cp1252", errors="ignore"))

    # Convert note to markdown
    # ------------------------------------------------------------------
    # Create an object that handles a lot of the logic of parsing the page paths, content, etc
    md = fo.load_markdown_page("note")

    # The bulk of the conversion process happens here
    md.ConvertObsidianPageToMarkdownPage()

    # The frontmatter was stripped from the obsidian note prior to conversion
    # Add yaml frontmatter back in
    md.page = (frontmatter.dumps(frontmatter.Post("", **md.metadata))) + "\n" + md.page

    # Save file
    # ------------------------------------------------------------------
    # Create folder if necessary
    dst_path = fo.path["markdown"]["file_absolute_path"]
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    # Write markdown to file
    with open(dst_path, "w", encoding="utf-8") as f:
        f.write(md.page)

    # Recurse for every link in the current page
    # ------------------------------------------------------------------
    # Don't follow links if this would exceed max note depth
    iteration += 1
    if pb.gc("max_note_depth") > -1 and iteration > pb.gc("max_note_depth"):
        return

    # Don't follow links when the user tells us not to
    if "obs.html.tags" in md.metadata.keys() and "leaf_note" in md.metadata["obs.html.tags"]:
        return

    for link_fo in md.links:
        if link_fo is False or link_fo.processed_ntm is True:
            if pb.gc("toggles/verbose_printout", cached=True):
                if link_fo is False:
                    print("\t" * log_level, f"(ntm) Skipping converting {link_fo.link}, link not internal or not valid.")
                else:
                    print("\t" * log_level, f"(ntm) Skipping converting {link_fo.link}, already processed.")
            continue

        # Mark the file as processed so that it will not be processed again at a later stage
        link_fo.processed_ntm = True

        # Convert the note that is linked to
        if pb.gc("toggles/verbose_printout", cached=True):
            print(
                "\t" * log_level,
                f"found link {link_fo.path['note']['file_absolute_path']} (through parent {fo.path['note']['file_absolute_path']})",
            )

        pb.init_state(action="n2m", loop_type="note", current_fo=link_fo, subroutine="crawl_obsidian_notes_and_convert_to_markdown")
        crawl_obsidian_notes_and_convert_to_markdown(link_fo, pb, log_level=log_level, iteration=iteration)
        pb.reset_state()


# @extra_info()
def crawl_markdown_notes_and_convert_to_html(fo: "FileObject", pb, backlink_node=None, log_level=1, capture_in_jar=False):
    """This functions converts a markdown page to an html file and calls itself on any local markdown links it finds in the page."""

    if pb.gc("toggles/stdout_current_file", cached=True):
        print(fo.path["markdown"]["file_absolute_path"].as_posix().encode("cp1252", errors="ignore"))

    # Convert and export page, and collect links to other markdown pages found in the page.
    # ------------------------------------------------------------------
    node, md_links = md2html.convert_markdown_page_to_html_and_export(fo, pb, backlink_node, log_level, capture_in_jar)

    # Recurse for every link in the current page
    # ------------------------------------------------------------------
    for link_fo in md_links:
        if not link_fo.is_valid_note("markdown"):
            continue

        # Convert the note that is linked to
        if pb.gc("toggles/verbose_printout", cached=True):
            print("\t" * (log_level + 1), f"html: initiating conversion for {link_fo.fullpath('markdown')} (parent {fo.fullpath('markdown')})")

        pb.init_state(action="m2h", loop_type="md_note", current_fo=link_fo, subroutine="crawl_markdown_notes_and_convert_to_html")
        crawl_markdown_notes_and_convert_to_html(link_fo, pb, backlink_node=node, log_level=log_level)
        pb.reset_state()


def run_post_processing(pb):
    post_processing_modules = pb.gc("toggles/features/post_processing")
    if len(post_processing_modules) > 0:
        if verbose_enough("info", pb.verbosity):
            print("> POST-PROCESSING:")
    for module in post_processing_modules:
        print(f"\t> {module['module']}")
        if module["module"] == "md_markdown_callouts":
            post_processing.convert_markdown_output(
                pb.paths["md_folder"],
                convert_function=post_processing.obs_callout_to_markdown_callout,
                arg_dict={"strict_line_breaks": (not pb.gc("toggles/strict_line_breaks"))},  # don't add line breaks if we already add them, because they will double up
            )
        else:
            raise Exception(f"Unknown processing module of {module['module']}")

    if len(post_processing_modules) > 0:
        if verbose_enough("info", pb.verbosity):
            print("< POST-PROCESSING: Done")
