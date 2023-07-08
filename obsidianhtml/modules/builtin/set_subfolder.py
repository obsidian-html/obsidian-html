import os
import yaml
import json

from pathlib import Path

from ..base_classes import ObsidianHtmlModule

from ...lib import (
    OpenIncludedFile,
    YamlIndentDumper,
    get_obshtml_appdir_folder_path,
    get_default_appdir_config_yaml_path,
)


class SetSubfolderModule(ObsidianHtmlModule):
    """
    This module replaces any html_url_prefix settings when `--subfolder <subfolder>` is configured on the commandline
    """

    @staticmethod
    def requires():
        return tuple(["config.yml", "arguments.yml"])

    @staticmethod
    def provides():
        return tuple(["config.yml"])

    @staticmethod
    def alters():
        return tuple()

    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def integrate_save(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def accept(self, module_data_folder):
        arguments = self.modfile("arguments.yml").read().from_yaml()
        if "subfolder" not in arguments:
            self.print("DEBUG", f'Skipped module {self.nametag} because "--subfolder" was not passed in')
            return False
        return True

    def run(self):
        arguments = self.modfile("arguments.yml").read().from_yaml()
        subfolder = arguments["subfolder"]

        print(subfolder)
        exit()
        # Set/overwrite html_url_prefix
        if subfolder != "":
            if subfolder[0] != "/":
                subfolder = "/" + subfolder
            if subfolder[-1] == "/":
                subfolder = subfolder[:-1]
            config["html_url_prefix"] = subfolder
            print_set_var(config, "html_url_prefix", reason="provided by user through commandline", category="info")
