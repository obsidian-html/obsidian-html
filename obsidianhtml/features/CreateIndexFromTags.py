import platform
import datetime

from ..core.FileObject import FileObject
from ..lib import slugify_path


def verbose(pb):
    return pb.gc("toggles/verbose_printout", cached=True) or pb.gc("toggles/features/create_index_from_tags/verbose", cached=True)


def CompileTagPageMarkdown(pb):
    # get settings
    files = pb.index.files
    settings = pb.gc("toggles/features/create_index_from_tags")

    method = settings["sort"]["method"]
    key_path = settings["sort"]["key_path"]
    value_prefix = settings["sort"]["value_prefix"]
    sort_reverse = settings["sort"]["reverse"]
    none_on_bottom = settings["sort"]["none_on_bottom"]

    include_folder_in_link = settings["styling"]["include_folder_in_link"]

    if verbose(pb):
        print("> FEATURE: CREATE INDEX FROM TAGS: Enabled")

    # Test input
    if not isinstance(settings["tags"], list):
        raise Exception("toggles/features/create_index_from_tags/tags should be a list")

    if len(settings["tags"]) == 0:
        raise Exception("Feature create_index_from_tags is enabled, but no tags were listed")

    # shorthand
    include_tags = settings["tags"]
    if verbose(pb):
        print("\tLooking for tags: ", include_tags)

    # Find notes with given tags
    _files = {}
    index_dict = {}
    for t in include_tags:
        index_dict[t] = []

    for k in files.keys():
        fo = files[k]

        # Don't parse if not parsable
        page_path = fo.fullpath("note")
        page_path_str = page_path.as_posix()
        if not fo.metadata["is_parsable_note"]:
            if verbose(pb):
                print(f"\t\tSkipping file, not parsable note: {page_path_str}")
            continue

        # Determine src file path
        if verbose(pb):
            print(f"\t\tParsing note {page_path_str}")

        # make mdpage object
        md = fo.load_markdown_page("note")
        md.StripCodeSections()

        metadata = md.metadata
        node_name = md.GetNodeName()
        node_id = pb.FileFinder.GetNodeId(pb, fo.path["markdown"]["file_relative_path"].as_posix())

        # Skip if not valid
        if not fo.is_valid_note("note"):
            continue

        # Check for each of the tags if its present
        # Skip if none matched
        matched = False
        for t in include_tags:
            if md.HasTag(t):
                if verbose(pb):
                    print(f"\t\tMatched note {k} on tag {t}")
                matched = True

        if matched is False:
            continue

        # determine sorting value
        sort_value = None
        if method not in ("none", "creation_time", "modified_time"):
            if method == "key_value":
                # key can be multiple levels deep, like this: level1:level2
                # get the value of the key
                key_found = True
                value = metadata
                for key in key_path.split(":"):
                    if key not in value.keys():
                        key_found = False
                        break
                    value = value[key]
                # only continue if the key is found in the current note, otherwise the
                # default sort value of None is kept
                if key_found:
                    # for a list find all items that start with the value prefix
                    # then remove the value_prefix, and check if we have 1 item left
                    if isinstance(value, list):
                        items = [x.replace(value_prefix, "", 1) for x in value if x.startswith(value_prefix)]
                        if len(items) == 1:
                            sort_value = items[0]
                            # done
                    if isinstance(value, str):
                        sort_value = value.replace(value_prefix, "", 1)
                    if isinstance(value, bool):
                        sort_value = str(int(value))
                    if isinstance(value, int) or isinstance(value, float):
                        sort_value = str(value)
                    if isinstance(value, datetime.datetime):
                        sort_value = value.isoformat()
            else:
                raise Exception(f"Sort method {method} not implemented. Check spelling.")

        # Get sort_value from files dict
        if method in ("creation_time", "modified_time"):
            # created time is not really accessible under Linux, we might add a case for OSX
            if method == "creation_time" and platform.system() != "Windows" and platform.system() != "Darwin":
                raise Exception(f'Sort method of "create_time" under toggles/features/create_index_from_tags/sort/method is not available under {platform.system()}, only Windows.')
            sort_value = fo.metadata[method]

        if verbose(pb):
            print(f"\t\t\tSort value of note {k} is {sort_value}")

        # Add an entry into index_dict for each tag matched on this page
        # copy file to temp filetree for checking later
        _files[k] = files[k]

        # Add entry to our index dict so we can parse this later
        # do this once for each tag, so each tag listing gets a link to this note
        for t in include_tags:
            if not md.HasTag(t):
                continue

            index_dict[t].append(
                {
                    "file_key": k,
                    "node_id": node_id,
                    "md_rel_path_str": fo.path["markdown"]["file_relative_path"].as_posix(),
                    "graph_name": node_name,
                    "sort_value": sort_value,
                }  # depr?
            )

    if len(_files.keys()) == 0:
        raise Exception("No notes found with the given tags.")

    if verbose(pb):
        print("\tBuilding index.md")

    index_md_content = ""
    for t in index_dict.keys():
        # Add header
        index_md_content += f"## {t}\n"

        # shorthand
        notes = index_dict[t]

        # fill in none types
        # - get max value
        input_val = ""
        max_val = ""
        for n in notes:
            if n["sort_value"] is None:
                continue
            if n["sort_value"] > max_val:
                max_val = n["sort_value"]
        max_val += "Z"

        # - determine if we need to give max val or min val
        if none_on_bottom:
            input_val = max_val
            if sort_reverse:
                input_val = ""
        else:
            input_val = ""
            if sort_reverse:
                input_val = max_val

        # - fill in none types
        for n in notes:
            if n["sort_value"] is None:
                n["sort_value"] = input_val

        # Sort notes
        notes = sorted(index_dict[t], key=lambda note: note["sort_value"], reverse=sort_reverse)

        # Add to index content
        for n in notes:
            # set link name
            link_name = n["file_key"][:-3]
            if not include_folder_in_link:
                link_name = n["file_key"][:-3].split("/")[-1]

            # Add to index content
            index_md_content += f"- [[{link_name}|{n['graph_name']}]]\n"
        index_md_content += "\n"

    # store md in pb for retrieval later on
    pb.jars["tags_page_markdown"] = index_md_content

    return index_md_content, index_dict


def CreateIndexFromTags(pb):
    # get settings
    paths = pb.paths
    settings = pb.gc("toggles/features/create_index_from_tags")

    # method          = settings['sort']['method']
    # key_path        = settings['sort']['key_path']
    # value_prefix    = settings['sort']['value_prefix']
    # sort_reverse    = settings['sort']['reverse']
    # none_on_bottom  = settings['sort']['none_on_bottom']

    if verbose(pb):
        print("> FEATURE: CREATE INDEX FROM TAGS: Enabled")

    # We'll need to write a file to the obsidian folder
    # This is not good if we don't target the temp folder (copy_vault_to_tempdir = True)
    # Because we don't want to mess around in people's vaults.
    # So disable this feature if that setting is turned off
    if pb.gc("copy_vault_to_tempdir") is False:
        raise Exception(
            "The feature 'CREATE INDEX FROM TAGS' needs to write an index file to the obsidian path. We don't want to write in your vault, so in order to use this feature set 'copy_vault_to_tempdir: True' in your config."
        )

    # shorthand
    include_tags = settings["tags"]
    if verbose(pb):
        print("\tLooking for tags: ", include_tags)

    # set output path (unless use_as_homepage is configured, see below)
    rel_path = settings["rel_output_path"]
    index_dst_path = paths["obsidian_folder"].joinpath(rel_path).resolve()

    # overwrite defaults
    if settings["use_as_homepage"]:
        if verbose(pb):
            print("\tWill overwrite entrypoints: obsidian_entrypoint, rel_obsidian_entrypoint")

        rel_path = "__tags_index.md"
        index_dst_path = paths["obsidian_folder"].joinpath(rel_path).resolve()
        paths["obsidian_entrypoint"] = index_dst_path
        paths["rel_obsidian_entrypoint"] = paths["obsidian_entrypoint"].relative_to(paths["obsidian_folder"])
        pb.paths = paths

    if verbose(pb):
        print("\tWill write the note index to: ", index_dst_path)

    md_content, index_dict = CompileTagPageMarkdown(pb)

    # write content to markdown file
    index_dst_path.parent.mkdir(exist_ok=True)
    with open(index_dst_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # add file to file tree
    fo_index_dst_path = FileObject(pb)
    fo_index_dst_path.init_note_path(index_dst_path)
    fo_index_dst_path.init_markdown_path()
    pb.index.files[rel_path] = fo_index_dst_path

    # [17] Build graph node/links
    if pb.gc("toggles/features/create_index_from_tags/add_links_in_graph_tree", cached=True):
        if verbose(pb):
            print("\tAdding graph links between index.md and the matched notes")

        node = pb.index.network_tree.NewNode()
        node["name"] = pb.gc("toggles/features/create_index_from_tags/homepage_label").capitalize()

        if settings["use_as_homepage"]:
            node["id"] = "index"
            node["url"] = f'{pb.gc("html_url_prefix")}/index.html'
        else:
            node["id"] = "tag_index"
            node["url"] = fo_index_dst_path.get_link("html")

        pb.index.network_tree.add_node(node)
        bln = node
        for t in index_dict.keys():
            for n in index_dict[t]:
                node = pb.index.network_tree.NewNode()
                node["id"] = n["node_id"]
                node["name"] = n["graph_name"]
                node["url"] = f'{pb.gc("html_url_prefix")}/{slugify_path(n["md_rel_path_str"][:-3])}.html'
                pb.index.network_tree.add_node(node)

                link = pb.index.network_tree.NewLink()
                link["source"] = bln["id"]
                link["target"] = node["id"]
                pb.index.network_tree.AddLink(link)

    if verbose(pb):
        print("< FEATURE: CREATE INDEX FROM TAGS: Done")

    return pb
