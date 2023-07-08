import os
import yaml

from pathlib import Path

from ...lib import pushd, WriteFileLog

from ...core.NetworkTree import NetworkTree
from ...core.FileObject import FileObject


from ..base_classes import ObsidianHtmlModule


class GetFileListModule(ObsidianHtmlModule):
    """
    This module will create the index/files.json file, which lists all the files in the source folder (vault or md folder).
    If included_folders is defined, it will limit itself to those sub(!)folders.
    Once that list exists, the exluded file (by excluded_glob) will be filtered out.
    """

    @staticmethod
    def requires():
        return tuple(["paths.json", "config.yml"])

    @staticmethod
    def provides():
        return tuple(["index/files.json", "index/excluded_files.json", "index/markdown_files.json"])

    @staticmethod
    def alters():
        return tuple()

    def define_mod_config_defaults(self):
        self.mod_config["include_glob"] = {
            "value": "*",
            "description": "Only include the files in the input folder that matches this glob. Default: all.",
            "example_value": [
                "/Home.md",  # specific file
                "Blog/**/*",  # any folder with name Blog, and all its contents (recursively)
                "subfolder/*",  # any file directly under any folder named "subfolder"
            ],
        }
        self.mod_config["exclude_glob"] = {
            "value": [
                ".obsidian/**/*",
                ".trash/**/*",
                ".DS_Store/**/*",
                ".git/**/*",
            ],
            "description": [
                "After included_glob is applied, excluded_glob is applied to filter out files.",
            ],
        }

    def accept(self, module_data_folder):
        """This function is run before run(), if it returns False, then the module run is skipped entirely. Any other value will be accepted"""
        return

    def glob_find(self, folder, glob_list):
        # ensure folder is a Path object
        folder = Path(folder)

        # find files
        found_files = []
        for glob_line in glob_list:
            # rglob does not support specific file matching. we fix this by allowing the "/file.md" syntax.
            # in this case we use glob instead of rglob
            if glob_line[0] == "/":
                glob_line = glob_line[1:]
                found_files = found_files + [x.as_posix() for x in folder.glob(glob_line)]
            else:
                found_files = found_files + [x.as_posix() for x in folder.rglob(glob_line)]

        # make unique & sort
        found_files = list(set(found_files))
        found_files.sort()

        return found_files

    def run(self):
        # get paths
        paths = self.modfile("paths.json").read().from_json()
        for key, value in paths.items():
            paths[key] = Path(value)

        # get all included files from input_folder
        included_files = self.glob_find(paths["input_folder"], self.value_of("include_glob"))

        # get all excluded files
        excluded_files = self.glob_find(paths["input_folder"], self.value_of("exclude_glob"))

        # get all included files minus excluded files
        selected_files = [x for x in included_files if x not in excluded_files]
        selected_files.sort()

        # remove dirs
        selected_files = [x for x in selected_files if Path(x).is_dir() == False]

        # check that the entrypoint file is not being filtered out
        if paths["entrypoint"].as_posix() not in selected_files:
            self.print("ERROR", f'You have configured {self.nametag} to filter out {paths["entrypoint"]}, which is your entrypoint. Correct this and run again.')
            exit(1)

        self.modfile("index/excluded_files.json", excluded_files).to_json().write()
        self.modfile("index/files.json", selected_files).to_json().write()

        # get markdown files
        markdown_files = [x for x in selected_files if x[-3:] == ".md"]
        self.modfile("index/markdown_files.json", markdown_files).to_json().write()

    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def integrate_save(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass
