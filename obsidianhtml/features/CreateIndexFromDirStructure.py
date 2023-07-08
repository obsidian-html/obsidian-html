import os
import yaml
import glob

import regex as re

from pathlib import Path
from functools import cache

from ..lib import simpleHash, pushd
from ..compiler.Templating import PopulateTemplate


class CreateIndexFromDirStructure:
    def __init__(self, pb, path):
        self.pb = pb
        self.html_url_prefix = pb.gc("html_url_prefix")
        self.root = path
        self.root_str = path.as_posix()
        self.verbose = pb.gc("toggles/verbose_printout") or pb.gc("toggles/features/create_index_from_dir_structure/verbose")

        self.exclude_subfolders = pb.gc("toggles/features/create_index_from_dir_structure/exclude_subfolders")
        self.exclude_files = pb.gc("toggles/features/create_index_from_dir_structure/exclude_files")
        self.build_exclude_list()

        self.tree = self.get_tree(path)
        self.tree = self.build_tree_recurse(self.tree)
        self.sort_tree()

        # used in BuildIndex
        self.uid = 0
        self.html = ""
        self.rel_output_path = None  # set by caller before running BuildIndex, search for pb.treeobj.rel_output_path

    def get_tree(self, path, files=None, folders=None):
        if files is None:
            files = []
        if folders is None:
            folders = []

        if isinstance(path, str):
            path = Path(path).resolve()

        path_str = path.as_posix()
        rel_path_str = path_str.replace(self.root_str, "", 1)

        return {"name": path.name, "path": path.as_posix(), "rel_path": rel_path_str, "folders": folders, "files": files}

    def build_exclude_list(self):
        """convert possible glob patterns to paths (str)"""

        # move to html output dir
        owd = pushd(self.root)

        # build lists
        exclude_folders = []
        for line in self.exclude_subfolders:
            exclude_folders += glob.glob(line, recursive=True)
        self.exclude_subfolders_str = list(set(exclude_folders))

        exclude_files = []
        for line in self.exclude_files:
            exclude_files += glob.glob(line, recursive=True)
        self.exclude_files_str = list(set(exclude_files))

        # print results
        if self.verbose:
            print(f"\t\tRoot used for glob pattern expansion: {self.root}")
            print("\n\t\tExcluded Folders (configured):")
            print(yaml.dump(self.exclude_subfolders))
            print("\n\t\tExcluded Files (configured):")
            print(yaml.dump(self.exclude_files))
            print("\n\t\tExcluded Folders (expanded from glob patterns and found):")
            print(yaml.dump(self.exclude_subfolders_str))
            print("\n\t\tExcluded Files (expanded from glob patterns and found):")
            print(yaml.dump(self.exclude_files_str))

        # move back to OG cwd
        os.chdir(owd)

    def build_tree_recurse(self, tree):
        verbose = self.verbose

        for path in Path(tree["path"]).resolve().glob("*"):
            # Exclude configured subfolders
            _continue = False
            for folder in self.exclude_subfolders_str:
                excl_folder_path = self.root.joinpath(folder)
                if path.resolve().is_relative_to(excl_folder_path):
                    if verbose:
                        print(f"\tExcluded folder {excl_folder_path}: Excluded file {path.name}.")
                    _continue = True
                    break
            if _continue:
                continue

            # for dir: create a subtree
            if path.is_dir():
                new_branch = self.build_tree_recurse(self.get_tree(path))
                tree["folders"].append(new_branch)
                continue

            # exclude files
            for ef in self.exclude_files_str:
                excl_file_path = self.root.joinpath(ef)
                if excl_file_path == path:
                    if verbose:
                        print(f"\tExcluded file {excl_file_path}.")
                    _continue = True
                    break
            if _continue:
                continue

            # set name to graph name if is note
            name = path.stem
            is_note = False
            if path.suffix == ".html":
                path_key = path.relative_to(self.pb.paths["html_output_folder"]).as_posix().replace(".html", ".md")
                if self.pb.gc("toggles/force_filename_to_lowercase", cached=True):
                    path_key = path_key.lower()

                fo = None
                try:  # html might be exported and not have a corresponding note
                    fo = self.pb.index.files[path_key]
                    name = fo.md.GetNodeName()
                except:
                    try:
                        fo = self.pb.index.aliased_files[path_key]
                        name = fo.md.GetNodeName()
                    except:
                        print(13, path_key)  # , self.pb.index.files.keys())

                if fo is not None:
                    is_note = fo.metadata["is_note"]

            # append file
            path_str = path.as_posix()
            rel_path_str = path_str.replace(self.root_str, "", 1)

            tree["files"].append({"name": path.stem, "suffix": path.suffix, "graph_name": name, "path": path.as_posix(), "rel_path": rel_path_str, "is_note": is_note})

        return tree

    def sort_tree(self):
        def _recurse(tree):
            tree["folders"] = sorted(tree["folders"], key=lambda d: d["name"])
            tree["files"] = sorted(tree["files"], key=lambda d: d["name"])
            for folder in tree["folders"]:
                _recurse(folder)

        _recurse(self.tree)

    def in_tree(self, path, subpath):
        path_parts = [x for x in path.split("/") if x]
        subpath_parts = [x for x in subpath.split("/") if x]

        if len(subpath_parts) > len(path_parts):
            return False

        for i, part in enumerate(subpath_parts):
            if part != path_parts[i]:
                return False

        return True

    def get_dir(self, path):
        return "/" + "/".join([x for x in path.split("/") if x][:-1])

    @cache
    def check_has_folder_note(self, folder_abs_path_str):
        settings = self.pb.gc("toggles/features/folder_notes", cached=True)
        if settings["enabled"] is False:
            return (False, "")

        folder_abs_path = Path(folder_abs_path_str)
        note_folder_abs_path = folder_abs_path
        if settings["placement"] == "outside folder":
            note_folder_abs_path = folder_abs_path.parent

        name = folder_abs_path.stem + ".html"
        if settings["naming"] != "folder name":
            name = f"{settings['naming']}.html"

        abs_path = note_folder_abs_path.joinpath(name)
        return (abs_path.exists(), abs_path)

    def check_is_folder_note(self, note_abs_path):
        settings = self.pb.gc("toggles/features/folder_notes", cached=True)
        if settings["enabled"] is False:
            return False

        # Homepage cannot be folder note
        if note_abs_path.relative_to(self.pb.paths["html_output_folder"]).as_posix() == "index.html":
            return False

        note_stem = note_abs_path.stem
        if settings["naming"] != "folder name":
            return note_stem == settings["naming"]

        elif settings["naming"] == "folder name":
            # find folder
            if settings["placement"] == "inside folder":
                if note_stem != note_abs_path.parent.stem:
                    return False
                else:
                    return True
            elif settings["placement"] == "outside folder":
                folder_path = note_abs_path.parent.joinpath(note_stem).resolve()
                return folder_path.exists()

        raise Exception("Unexpected escape from elif fence in check_is_folder_note()")

    def convert_abs_path_to_url(self, abs_path):
        rel_path = abs_path.relative_to(self.root)
        return f"{self.html_url_prefix}/{rel_path}"

    def BuildIndex(self, current_page="/"):
        # Get basic html that we will then edit to make it applicable for the current page.
        proto = self.BuildProtoIndex("/")

        # folder of the current page
        dir_path = self.get_dir(current_page)

        # -- set current folders to be opened
        dirs = dir_path.split("/")
        while dirs and dirs[-1]:
            cdp = "/".join(dirs)
            dirs.pop()
            dir_css_active = f"``css-dir-active-{cdp}``"
            proto = proto.replace(dir_css_active, "active")

        # remove unused tags
        safe_str = r"``css-dir-active-.*?``"
        proto = re.sub(safe_str, "", proto)

        # -- set active file
        file_css_active = f"``css-file-active-{current_page}``"
        proto = proto.replace(file_css_active, "active current_page_dirtree")

        safe_str = r"``css-file-active-.*?``"
        proto = re.sub(safe_str, "", proto)

        # -- set folder-note-active
        folder_note_active = f"``css-folder-note-active-{current_page}``"
        proto = proto.replace(folder_note_active, "active current_page_dirtree")

        safe_str = r"``css-folder-note-active-.*?``"
        proto = re.sub(safe_str, "", proto)

        # -- set folder-note-onclick active
        onclick_active = f"``onclick-folder-note-{current_page}``"
        proto = proto.replace(onclick_active, "toggle_dir(this.id)")

        # -- set folder-note-onclick inactive
        safe_str = r"``onclick-folder-note-.*?``"
        proto = re.sub(safe_str, "open_folder_note(this)", proto)

        return proto

    @cache
    def BuildProtoIndex(self, current_page="/"):
        def set_file_name(f, tab_level):
            if tab_level == 1 and f["name"] == "index":
                return self.pb.gc("toggles/features/create_index_from_dir_structure/homepage_label", cached=True)
            else:
                return f["graph_name"]

        def _recurse(tree, tab_level, path, current_page):
            html = ""

            if tab_level >= 0:
                # -- [#288] folder notes
                # if the folder is the parent of the current_page it needs to be opened when loading the page
                # a folder note folder needs slightly different design
                fnpf = ""
                folder_id = self.html_url_prefix + tree["rel_path"]

                # test if the folder being processed in this loop has an existing folder note
                has_folder_note, note_abs_path = self.check_has_folder_note(tree["path"])

                folder_note_rel_path_str = "-"
                if has_folder_note:
                    folder_note_rel_path_str = self.html_url_prefix + note_abs_path.as_posix().replace(self.root_str, "", 1)
                    fnpf = '<div class="fn_pf">*</div>'
                    url = self.convert_abs_path_to_url(note_abs_path)
                    onclick = f"``onclick-folder-note-{folder_note_rel_path_str}``"

                    html += (
                        "\t" * tab_level
                        + f'<button id="folder-{self.uid}" class="dir-button folder_note ``css-dir-active-{folder_id}`` ``css-folder-note-active-{folder_note_rel_path_str}``" href="{url}" onclick="{onclick}">'
                        + f'<div class="file-icon"></div>'
                        + f'{fnpf}{tree["name"]}</button>\n'
                    )
                else:
                    html += (
                        "\t" * tab_level
                        + f'<button id="folder-{self.uid}" class="dir-button ``css-dir-active-{folder_id}``" onclick="toggle_dir(this.id)">'
                        + f'<div class="file-icon"></div>'
                        + f'{tree["name"]}</button>\n'
                    )

                html += "\t" * tab_level + f'<div id="folder-container-{self.uid}" class="dir-container requires_js ``css-dir-active-{folder_id}``" path="{path}">\n'

            tab_level += 1
            self.uid += 1

            for folder in tree["folders"]:
                html += _recurse(folder, tab_level, "/".join((path, folder["name"])), current_page)

            html += "\t" * tab_level + '<ul class="dir-list">\n'
            tab_level += 1

            excluded_paths = self.pb.gc("toggles/features/create_index_from_dir_structure/exclude_files", cached=True)
            for f in tree["files"]:
                if self.check_is_folder_note(Path(f["path"])):
                    continue

                rel_path = f["rel_path"][1:]
                rel_path = rel_path.replace("?", "%3F")
                file_id = self.html_url_prefix + f["rel_path"]
                name = set_file_name(f, tab_level)

                if rel_path in excluded_paths:
                    continue

                # get link adjustment code
                class_list = ""
                external_blank_html = ""
                if Path(rel_path).suffix != ".html":
                    class_list = 'class="external-link"'
                    if self.pb.gc("toggles/external_blank"):
                        external_blank_html = 'target="_blank" '

                non_note_class = ""
                if not f["is_note"]:
                    non_note_class = " non-md-file"
                    name += f["suffix"]

                html += (
                    "\t" * tab_level
                    + f'<li><div class="file-icon{non_note_class}"></div><a class="``css-file-active-{file_id}``" href="{self.html_url_prefix}/{rel_path}" {external_blank_html} {class_list}>{name}</a></li>\n'
                )

            tab_level -= 1
            html += "\t" * tab_level + "</ul>\n"
            tab_level -= 1
            if tab_level >= 0:
                html += "\t" * tab_level + "</div>\n"

            return html

        self.uid = 0
        html = _recurse(self.tree, -1, "" + self.html_url_prefix, current_page)

        return f'<div id="dirtree">{html}</div>'

    def WriteIndex(self):
        output_path = self.root.joinpath(self.rel_output_path).resolve()

        page_depth = len(self.rel_output_path.split("/")) - 1

        # make parent folders if necessary
        output_path.parent.mkdir(exist_ok=True)

        # write html to output
        pb = self.pb

        if pb.gc("toggles/features/graph/enabled", cached=True):
            graph_template = (
                pb.graph_template.replace("{id}", simpleHash(self.html))
                .replace("{pinnedNode}", "dirtree")
                .replace("{pinnedNodeGraph}", "dirtree")
                .replace("{html_url_prefix}", self.html_url_prefix)
                .replace("{graph_coalesce_force}", pb.gc("toggles/features/graph/coalesce_force", cached=True))
                .replace("{graph_classes}", "hidden")
            )

            self.html += f"\n{graph_template}\n"

        html = PopulateTemplate(
            pb,
            "none",
            pb.dynamic_inclusions,
            pb.html_template,
            content=self.html,
            container_wrapper_class_list=["single_tab_page-left-aligned"],
        )

        html = (
            html.replace("{pinnedNode}", "dirtree")
            .replace("{left_pane}", "")
            .replace("{right_pane}", "")
            .replace("{{navbar_links}}", "\n".join(pb.navbar_links))
            .replace("{dirtree_main_path}", self.rel_output_path)
            .replace("{page_depth}", str(page_depth))
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
