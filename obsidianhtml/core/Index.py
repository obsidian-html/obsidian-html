import glob
import os
import json

from pathlib import Path

from ..lib import pushd, WriteFileLog

from .NetworkTree import NetworkTree
from .FileObject import FileObject


class Index:
    def __init__(self, pb):
        # integrate with picknickbasket
        self.pb = pb
        self.pb.index = self

        # setup network tree, which keeps track of the graph (nodes and the links between them)
        self.network_tree = NetworkTree(self)

        # setup the file tree, which provides detailed information on the files in the vault/output folders
        self.init_file_tree()
        self.import_files_into_file_tree()

    def init_file_tree(self):
        """This method sets up everything needed for the file tree. It does not yet load the files into the file tree"""
        self.files = {}  # contains every file exactly once (currently twice in the case of the index file)
        self.aliased_files = {}  # files known under a different path_key, such as for slugged file paths

    def compile_html_relpath_lookup_table(self):
        self.fo_by_html_relpath = {}
        for fo in self.files.values():
            rel_path = fo.path["html"]["file_relative_path"].as_posix()
            self.fo_by_html_relpath[rel_path] = fo

    def import_files_into_file_tree(self):
        """This method reads all the files in the input folders - minus the excluded files - converts them into file objects, and puts them in the self.files dict"""
        pb = self.pb

        module_data_folder = self.pb.module_data_folder

        with open(module_data_folder + "/paths.json", "r") as f:
            paths = json.loads(f.read())
        input_folder = Path(paths["input_folder"])

        with open(module_data_folder + "/index/files.json", "r") as f:
            files = json.loads(f.read())

        # # add index.md when converting straight from md to html
        # if not pb.gc("toggles/compile_md", cached=True):
        #     print(input_folder.joinpath("index.md"))
        #     files.append(input_folder.joinpath("index.md"))

        for file in files:
            file = Path(file)
            if file.is_dir():
                continue

            fo = FileObject(pb)

            # Compile paths
            if pb.gc("toggles/compile_md", cached=True):
                # compile note --> markdown
                fo.init_note_path(file)
                fo.compile_metadata(fo.path["note"]["file_absolute_path"], cached=True)

                if pb.gc("toggles/compile_html", cached=True):
                    # compile markdown --> html (based on the given note path)
                    fo.init_markdown_path()
                    fo.compile_metadata(fo.path["markdown"]["file_absolute_path"].as_posix(), cached=True)

                # Add to tree
                self.add_file_object_to_file_tree(fo.path["note"]["file_relative_path"].as_posix(), fo)
            else:
                # compile markdown --> html (based on the found markdown path)
                fo.init_markdown_path(file)
                fo.compile_metadata(fo.path["markdown"]["file_absolute_path"], cached=True)

                # Add to tree
                self.add_file_object_to_file_tree(fo.path["markdown"]["file_relative_path"].as_posix(), fo)

    def add_file_object_to_file_tree(self, rel_path, obj):
        if self.pb.gc("toggles/force_filename_to_lowercase", cached=True):
            rel_path = rel_path.lower()
        self.files[rel_path] = obj
