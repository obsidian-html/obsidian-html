from ..lib import CreateStaticFilesFolders, OpenIncludedFile, OpenIncludedFileBinary, get_html_url_prefix
from ..features.SidePane import get_side_pane_id_by_content_selector, get_content_name_by_pane_id


def ExportStaticFiles(pb):
    (obsfolder, static_folder, data_folder, rss_folder) = CreateStaticFilesFolders(pb.paths["html_output_folder"])

    # define files to be copied over (standard copy, static_folder)
    copy_file_list = [
        ["svgs/external.svg", "external.svg"],
        ["svgs/hashtag.svg", "hashtag.svg"],
        ["html/css/taglist.css", "taglist.css"],
        ["rss/rss.svg", "rss.svg"],
        ["index_from_dir_structure/dirtree.svg", "dirtree.svg"],
        ["js/obsidian_core.js", "obsidian_core.js"],
        ["smiles/smiles.js", "smiles.js"],
        ["js/encoding.js", "encoding.js"],
        ["index_from_dir_structure/dirtree.js", "dirtree.js"],
    ]

    css_files_list = [["html/css/global_main.css", "global_main.css"]]

    if pb.ConfigManager.feature_is_enabled("graph", cached=True):
        copy_file_list.append(["imported/3d-force-graph.v1.70.10.min.js", "3d-force-graph.js"])
        css_files_list.append(["graph/graph.css", "graph.css"])
        copy_file_list.append(["graph/graph.svg", "graph.svg"])
        # copy_file_list.append(['graph/default_grapher_2d.js', 'default_grapher_2d.js'])
        # copy_file_list.append(['graph/default_grapher_3d.js', 'default_grapher_3d.js'])

    if pb.ConfigManager.feature_is_enabled("mermaid_diagrams", cached=True):
        pass
        # copy_file_list.append(["imported/mermaid.9.0.1.min.js", "mermaid.9.0.1.min.js"])
        # copy_file_list.append(["imported/mermaid.9.0.1.min.js.map", "mermaid.9.0.1.min.js.map"])
        # copy_file_list.append(["html/css/mermaid.css", "mermaid.css"])

    if pb.ConfigManager.feature_is_enabled("smiles", cached=True):
        copy_file_list.append(["smiles/smiles.js", "smiles.js"])

    if pb.ConfigManager.feature_is_enabled("code_highlight", cached=True):
        css_files_list.append(["html/css/codehilite.css", "codehilite.css"])

    if pb.ConfigManager.feature_is_enabled("search", cached=True):
        copy_file_list.append(["search/search.svg", "search.svg"])
        copy_file_list.append(["search/pako.js", "pako.js"])
        copy_file_list.append(["search/search.js", "search.js"])
        css_files_list.append(["search/search.css", "search.css"])
        copy_file_list.append(["imported/flexsearch.v0.7.2.bundle.js", "flexsearch.bundle.js"])

    # if pb.ConfigManager.feature_is_enabled('math_latex', cached=True):
    #     copy_file_list.append(['latex/load_mathjax.js', 'load_mathjax.js'])
    #     copy_file_list.append(['imported/mathjax.v3.es5.tex-chtml.js', 'tex-chtml.js'])

    if pb.ConfigManager.feature_is_enabled("callouts", cached=True):
        css_files_list.append(["html/css/callouts.css", "callouts.css"])

    if pb.gc("toggles/features/styling/layout", cached=True) == "documentation":
        copy_file_list.append(["js/load_dirtree_footer.js", "load_dirtree_footer.js"])

    if pb.gc("toggles/features/styling/layout", cached=True) == "tabs":
        copy_file_list.append(["js/obsidian_tabs_footer.js", "obsidian_tabs_footer.js"])

    # create master.css file
    css_files_list += [
        [f'html/layouts/{pb.gc("_css_file")}', "main.css"],
        ["html/themes/theme-obsidian.css", "theme-obsidian.css"],
        ["html/css/global_overwrites.css", "global_overwrites.css"],
    ]
    css = ""
    for filepath, _ in css_files_list:
        css += "\n\n" + OpenIncludedFile(filepath)

    copy_file_list.append([{"type": "contents", "contents": css}, "master.css"])

    # copy static files over to the static folder
    for file in copy_file_list:
        file_record = file[0]
        file_name = file[1]
        contents = ""

        # Get file contents
        if isinstance(file_record, dict):
            # ... from absolute path
            if file_record["type"] == "absolute_path_str":
                with open(file_record["path"], "r", encoding="utf-8") as f:
                    contents = f.read()
            # ... from file_record itself
            elif file_record["type"] == "contents":
                contents = file_record["contents"]
            else:
                raise Exception("ERROR: file_record type in unknown")
        else:
            # ... from package
            contents = OpenIncludedFile(file_record)

        # Define dest path and html_url_prefix
        dst_path = static_folder.joinpath(file_name)
        html_url_prefix = get_html_url_prefix(pb, abs_path_str=dst_path)

        # Set pane divs
        toc_pane_div = get_side_pane_id_by_content_selector(pb, "toc")
        dir_index_pane_div = get_side_pane_id_by_content_selector(pb, "dir_index")

        # Templating
        if file_name in ("master.css", "main.css", "global_main.css", "obsidian_core.js", "search.js", "search.css"):
            url_mode = "absolute"
            if pb.gc("toggles/relative_path_html"):
                url_mode = "relative"

            contents = (
                contents.replace("{html_url_prefix}", html_url_prefix)
                .replace("{configured_html_url_prefix}", pb.configured_html_prefix)
                .replace("{no_tabs}", str(int(pb.gc("toggles/no_tabs", cached=True))))
                .replace("{only_show_for_multiple_headers}", str(int(pb.gc("toggles/features/table_of_contents/only_show_for_multiple_headers", cached=True))))
                .replace("{close_right_pane_if_empty}", str(int(pb.gc("toggles/features/side_pane/right_pane/close_if_empty", cached=True))))
                .replace("{close_left_pane_if_empty}", str(int(pb.gc("toggles/features/side_pane/left_pane/close_if_empty", cached=True))))
                .replace("{relative_paths}", str(int(pb.gc("toggles/relative_path_html"))))
                .replace("{documentation_mode}", str(int(pb.gc("toggles/features/styling/layout") == "documentation")))
                .replace("{mermaid_enabled}", str(int(pb.gc("toggles/features/mermaid_diagrams/enabled"))))
                .replace("{toc_pane_div}", toc_pane_div)
                .replace("{dir_index_pane_div}", dir_index_pane_div)
                .replace("{gzip_hash}", pb.gzip_hash)
                .replace("{url_mode}", url_mode)
                .replace("{try_preload}", str(int(pb.gc("toggles/features/search/try_preload"))))
            )
            contents = (
                contents.replace("__accent_color__", pb.gc("toggles/features/styling/accent_color", cached=True))
                .replace("__loading_bg_color__", pb.gc("toggles/features/styling/loading_bg_color", cached=True))
                .replace("__max_note_width__", pb.gc("toggles/features/styling/max_note_width", cached=True))
                .replace("__left_pane_active_width__", pb.gc("toggles/features/side_pane/left_pane/width", cached=True))
                .replace("__right_pane_active_width__", pb.gc("toggles/features/side_pane/right_pane/width", cached=True))
            )

        if file_name in ("smiles.js",):
            contents = (
                contents.replace("{smiles_theme}", pb.gc("toggles/features/smiles/theme", cached=True))
                .replace("{smiles_width}", pb.gc("toggles/features/smiles/width", cached=True))
                .replace("{smiles_height}", pb.gc("toggles/features/smiles/height", cached=True))
            )

        # Write to dest
        with open(dst_path, "w", encoding="utf-8") as f:
            f.write(contents)

    # copy binary files to dst (byte copy, static_folder)
    copy_file_list_byte = [
        ["html/fonts/SourceCodePro-Regular.ttf", "SourceCodePro-Regular.ttf"],
        ["html/fonts/Roboto-Regular.ttf", "Roboto-Regular.ttf"],
    ]
    for file_name in copy_file_list_byte:
        c = OpenIncludedFileBinary(file_name[0])
        with open(static_folder.joinpath(file_name[1]), "wb") as f:
            f.write(c)

    # Custom copy

    c = OpenIncludedFileBinary("html/favicon.ico")
    with open(pb.paths["html_output_folder"].joinpath("favicon.ico"), "wb") as f:
        f.write(c)

    if pb.gc("toggles/features/graph/enabled", cached=True):
        # create grapher files
        dynamic_imports = "// DYNAMIC\n" + ("/" * 79) + "\n"
        grapher_list = []
        grapher_hash = []

        graph_folder = static_folder.joinpath("graphers/")
        graph_folder.mkdir(parents=True, exist_ok=True)

        for grapher in pb.graphers:
            # save file in graphers folder
            dst_path = graph_folder.joinpath(f'{grapher["id"]}.js')
            with open(dst_path, "w", encoding="utf-8") as f:
                f.write(grapher["contents"])

            # add to dynamic imports in grapher.js
            dynamic_imports += f"import * as grapher_{grapher['id']} from './graphers/{grapher['id']}.js';\n"

            # add to grapher list
            grapher_list.append("{'id': '" + grapher["id"] + "', 'name': '" + grapher["name"] + "', 'module': grapher_" + grapher["id"] + "}")
            grapher_hash.append("'" + grapher["id"] + "': " + grapher_list[-1])

        dynamic_imports += "\n"
        dynamic_imports += f"const CONFIGURED_HTML_URL_PREFIX = '{pb.configured_html_prefix}';\n"
        if pb.gc("toggles/relative_path_html"):
            dynamic_imports += 'const URL_MODE = "relative";\n'
        else:
            dynamic_imports += 'const URL_MODE = "absolute";\n'
        dynamic_imports += "\n"

        grapher_list = "var graphers = [\n\t" + ",\n\t".join(grapher_list) + "\n]\n"
        grapher_hash = "var graphers_hash = {\n\t" + ",\n\t".join(grapher_hash) + "\n}\n"

        # create graph.js
        dst_path = static_folder.joinpath("graph.js")
        html_url_prefix = get_html_url_prefix(pb, abs_path_str=dst_path)

        graph_js = OpenIncludedFile("graph/graph.js")
        graph_js = (
            graph_js.replace("{html_url_prefix}", html_url_prefix)
            .replace("{coalesce_force}", pb.gc("toggles/features/graph/coalesce_force", cached=True))
            .replace("{no_tabs}", str(int(pb.gc("toggles/no_tabs", cached=True))))
        )
        graph_js = dynamic_imports + grapher_list + grapher_hash + graph_js

        with open(dst_path, "w", encoding="utf-8") as f:
            f.write(graph_js)


def PopulateTemplate(
    pb,
    node_id,
    dynamic_inclusions,
    template,
    content,
    html_url_prefix=None,
    title="",
    dynamic_includes=None,
    container_wrapper_class_list=None,
):
    # Cache
    if html_url_prefix is None:
        html_url_prefix = pb.gc("html_url_prefix")

    # Major components
    # header
    ht = pb.gc("toggles/features/styling/header_template")
    ht = f"html/templates/{ht}_header.html"
    template = template.replace("{header}", OpenIncludedFile(ht))
    template = template.replace("{toggle_left_pane_text}", f"Toggle {get_content_name_by_pane_id(pb, 'left_pane')} Pane")
    template = template.replace("{toggle_right_pane_text}", f"Toggle {get_content_name_by_pane_id(pb, 'right_pane')} Pane")

    # Header inclusions
    # make sure passed in inclusions are last in the list
    dynamic_inclusions_tail = dynamic_inclusions
    dynamic_inclusions = ""
    dynamic_inclusions += '<script src="' + html_url_prefix + '/obs.html/static/obsidian_core.js"></script>' + "\n"
    dynamic_inclusions += '<script src="' + html_url_prefix + '/obs.html/static/encoding.js"></script>' + "\n"
    dynamic_inclusions += '<link rel="stylesheet" href="' + html_url_prefix + '/obs.html/static/master.css" />' + "\n"

    if pb.ConfigManager.feature_is_enabled("smiles", cached=True):
        dynamic_inclusions += '<script src="https://unpkg.com/smiles-drawer@2.0.3/dist/smiles-drawer.min.js"></script>'
        dynamic_inclusions += '<script src="' + html_url_prefix + '/obs.html/static/smiles.js"></script>' + "\n"

    if pb.ConfigManager.feature_is_enabled("callouts", cached=True):
        pass
        # dynamic_inclusions += '<link rel="stylesheet" href="'+html_url_prefix+'/obs.html/static/callouts.css" />' + "\n"

    if pb.ConfigManager.feature_is_enabled("graph", cached=True):
        pass
        # dynamic_inclusions += '<link rel="stylesheet" href="'+html_url_prefix+'/obs.html/static/graph.css" />' + "\n"

    # if pb.ConfigManager.feature_is_enabled('code_highlight', cached=True):
    # dynamic_inclusions += '<link rel="stylesheet" href="'+html_url_prefix+'/obs.html/static/codehilite.css" />' + "\n"

    if pb.ConfigManager.feature_is_enabled("mermaid_diagrams", cached=True):
        # dynamic_inclusions += '<script src="' + html_url_prefix + '/obs.html/static/mermaid.9.0.1.min.js"></script>' + "\n"
        # dynamic_inclusions += '<link rel="stylesheet" href="'+html_url_prefix+'/obs.html/static/mermaid.css" />' + "\n"
        dynamic_inclusions += OpenIncludedFile("mermaid/init_mermaid.html") + "\n"

    if pb.ConfigManager.feature_is_enabled("math_latex", cached=True):
        # dynamic_inclusions += '<script src="'+html_url_prefix+'/obs.html/static/tex-chtml.js"></script>' + "\n"
        # dynamic_inclusions += '<script src="'+html_url_prefix+'/obs.html/static/load_mathjax.js"></script>' + "\n"
        dynamic_inclusions += OpenIncludedFile("latex/load_mathjax_header_template.html") + "\n"
        # dynamic_inclusions += '<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>' + "\n"

    if pb.ConfigManager.feature_is_enabled("search", cached=True):
        dynamic_inclusions += '<script src="' + html_url_prefix + '/obs.html/static/flexsearch.bundle.js"></script>' + "\n"
        dynamic_inclusions += '<script src="' + html_url_prefix + '/obs.html/static/pako.js"></script>' + "\n"
        dynamic_inclusions += '<script src="' + html_url_prefix + '/obs.html/static/search.js"></script>' + "\n"
        # dynamic_inclusions += '<link rel="stylesheet" href="'+html_url_prefix+'/obs.html/static/search.css" />' + "\n"

    if pb.capabilities_needed["directory_tree"]:
        dynamic_inclusions += '<script src="' + html_url_prefix + '/obs.html/static/dirtree.js"></script>' + "\n"

    dynamic_inclusions += dynamic_inclusions_tail + "\n"

    if dynamic_includes is not None:
        dynamic_inclusions += dynamic_includes

    # Footer Inclusions
    footer_js_inclusions = ""

    if pb.gc("toggles/features/styling/layout", cached=True) == "documentation":
        footer_js_inclusions += f'<script src="{html_url_prefix}/obs.html/static/load_dirtree_footer.js" type="text/javascript"></script>' + "\n"

    if pb.gc("toggles/features/styling/layout", cached=True) == "tabs":
        footer_js_inclusions += f'<script src="{html_url_prefix}/obs.html/static/obsidian_tabs_footer.js" type="text/javascript"></script>' + "\n"

    # Include toggled components
    if pb.ConfigManager.ShowIcon("rss"):
        code = OpenIncludedFile("rss/button_template.html")
        template = template.replace("{rss_button}", code)
    else:
        template = template.replace("{rss_button}", "")

    if pb.ConfigManager.ShowIcon("graph"):
        code = OpenIncludedFile("graph/button_template.html")
        template = template.replace("{graph_button}", code)
    else:
        template = template.replace("{graph_button}", "")

    if pb.ConfigManager.ShowIcon("search"):
        code = OpenIncludedFile("search/button_template.html")
        template = template.replace("{search_button}", code)
    else:
        template = template.replace("{search_button}", "")

    if pb.ConfigManager.ShowIcon("tags_page"):
        code = OpenIncludedFile("tags_page/button_template.html")
        template = template.replace("{tags_page_button}", code)
    else:
        template = template.replace("{tags_page_button}", "")

    if pb.ConfigManager.ShowIcon("theme_picker"):
        code = OpenIncludedFile("html/themes/button_template.html")
        template = template.replace("{theme_button}", code)
        code = OpenIncludedFile("html/themes/popup.html")
        template = template.replace("{theme_popup}", code)
    else:
        template = template.replace("{theme_button}", "")
        template = template.replace("{theme_popup}", "")

    if pb.ConfigManager.ShowIcon("create_index_from_dir_structure"):
        output_path = html_url_prefix + "/" + pb.gc("toggles/features/create_index_from_dir_structure/rel_output_path", cached=True)
        code = OpenIncludedFile("index_from_dir_structure/button_template.html")
        code = code.replace("{dirtree_index_path}", output_path)
        template = template.replace("{dirtree_button}", code)
    else:
        template = template.replace("{dirtree_button}", "")

    if pb.ConfigManager.feature_is_enabled("search", cached=True):
        template = template.replace("{search_html}", OpenIncludedFile("search/search.html"))
    else:
        template = template.replace("{search_html}", "")

    if pb.ConfigManager.feature_is_enabled("search", cached=True):
        template = template.replace("{search_html}", OpenIncludedFile("search/search.html"))
    else:
        template = template.replace("{search_html}", "")

    # Misc
    if title == "":
        title = pb.gc("site_name", cached=True)

    if container_wrapper_class_list is None:
        container_wrapper_class_list = []
    if pb.gc("toggles/no_tabs", cached=True):
        container_wrapper_class_list.append("single_tab_page")

    # Replace placeholders
    template = (
        template.replace("{node_id}", node_id)
        .replace("{title}", title)
        .replace("{dynamic_includes}", dynamic_inclusions)
        .replace("{dynamic_footer_includes}", pb.dynamic_footer_inclusions)
        .replace("{footer_js_inclusions}", footer_js_inclusions)
        .replace("{html_url_prefix}", html_url_prefix)
        .replace("{configured_html_url_prefix}", pb.configured_html_prefix)
        .replace("{container_wrapper_class_list}", " ".join(container_wrapper_class_list))
        .replace("{no_tabs}", str(int(pb.gc("toggles/no_tabs", cached=True))))
        .replace("{pinnedNode}", node_id)
        .replace("{{navbar_links}}", "\n".join(pb.navbar_links))
        .replace("{content}", content)
    )

    return template
    # Adding value replacement in content should be done in crawl_markdown_notes_and_convert_to_html,
    # Between the md.StripCodeSections() and md.RestoreCodeSections() statements, otherwise codeblocks can be altered.
