import glob
import os
import shutil

from pathlib import Path

from ...lib import pushd, WriteFileLog

from ...core.NetworkTree import NetworkTree
from ...core.FileObject import FileObject

from ..base_classes import ObsidianHtmlModule


class PrepareOutputFoldersModule(ObsidianHtmlModule):
    """
    This module will create the files.yml file, which lists all the files in the source folder (vault or md folder), minus the excluded files.
    It will also create the aliased_files.yml file, which contains references to files by an alias.
    """

    @staticmethod
    def requires():
        return tuple(["config.yml", "paths.json", "guid.txt"])

    @staticmethod
    def provides():
        return tuple()

    @staticmethod
    def alters():
        return tuple(["md_misc", "html_misc"])

    def define_mod_config_defaults(self):
        self.mod_config["clean_existing"] = {"value": True, "description": ["Files that exist in the output folders are deleted.", "Does nothing if clean_existing = True!"]}
        self.mod_config["fail_on_existing"] = {"value": False, "description": "Exit with error if output folders are not empty."}

    def accept(self, module_data_folder):
        """This function is run before run(), if it returns False, then the module run is skipped entirely. Any other value will be accepted"""
        return

    def run(self):
        # get paths
        paths = self.modfile("paths.json").read().from_json()
        for key, value in paths.items():
            paths[key] = Path(value)

        # remove previous output
        if self.value_of("clean_existing") is True:
            if self.gc("toggles/compile_md") and paths["md_folder"].exists():
                shutil.rmtree(paths["md_folder"])
            if paths["html_output_folder"].exists():
                shutil.rmtree(paths["html_output_folder"])

        # always clean the module_data_folder/versions folder
        guid = self.modfile("guid.txt").read().text()
        versions_folder = Path(self.module_data_folder).joinpath("versions")
        if versions_folder.exists():
            for subdir in [x for x in os.listdir(versions_folder) if x != guid]:
                shutil.rmtree(versions_folder.joinpath(subdir))
            if os.listdir(versions_folder) == []:
                versions_folder.rmdir()

        # fail if the folders are not empty
        def is_empty(path):
            if path.exists() is False:
                return True
            if len(os.listdir(path)) > 0:
                return False
            return True

        if self.value_of("fail_on_existing") is True:
            if self.gc("toggles/compile_md") and not is_empty(paths["md_folder"]):
                raise Exception(f'Output folder {paths["md_folder"]} is not empty. ({self.nametag}) was instructed to fail in that case')
            if not is_empty(paths["html_output_folder"]):
                raise Exception(f'Output folder {paths["html_output_folder"]} is not empty. ({self.nametag}) was instructed to fail in that case')

        # create output folders
        if self.gc("toggles/compile_md"):
            paths["md_folder"].mkdir(parents=True, exist_ok=True)
        paths["html_output_folder"].mkdir(parents=True, exist_ok=True)

    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def integrate_save(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass
