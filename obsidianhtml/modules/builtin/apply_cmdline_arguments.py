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


class ApplyCommandlineArgumentsModule(ObsidianHtmlModule):
    """
    Will (over)write config based on commandline arguments:
      -f <obs entrypoint> will set: obsidian_entrypoint_path_str
      -o <output dir> will set: html_output_folder_path_str, module_data_folder, md_folder_path_str
      --subdir <subdir> will set: html_url_prefix, html_output_folder_path_str
    """

    @staticmethod
    def requires():
        return tuple([])

    @staticmethod
    def provides():
        return tuple([])

    @staticmethod
    def alters():
        return tuple()

    def accept(self, module_data_folder):
        """This function is run before run(), if it returns False, then the module run is skipped entirely. Any other value will be accepted"""
        return

    def run(self, arguments):
        self.__verbosity__overwrite__ = "info"

        # this module should only be called for the case where an entrypoint is passed in
        if "-f" not in arguments["literals"]:
            self.print("ERROR", f"500: {self.nametag} was started because -f was supposedly present in arguments, but it is not found inside of the module")
            exit(-1)

        # get path info
        default_config_save_path = get_default_appdir_config_yaml_path()
        user_config_input_path = arguments["config_path"]

        # load user config
        user_config_output_path = None
        user_config = {}
        if user_config_input_path is not None:
            with open(user_config_input_path, "r") as f:
                user_config = yaml.safe_load(f.read())

        # set output path for user config
        # (either given input path, or default location)
        if user_config_input_path is None:
            user_config_output_path = default_config_save_path
        else:
            user_config_output_path = user_config_input_path

        # make new/alter config using entrypoint
        entrypoint_path_str = arguments["literals"]["-f"]
        entrypoint_path, entrypoint_abs_path_posix = self.test_entrypoint_path_exists(entrypoint_path_str)
        user_config["obsidian_entrypoint_path_str"] = entrypoint_abs_path_posix

        user_config_input_path = Path(user_config_input_path)
        user_config_output_path = Path(user_config_output_path)
        if user_config_input_path == user_config_output_path:
            self.print("INFO", f'Will alter existing config "{user_config_output_path.as_posix()}" using "{entrypoint_path_str}" as entrypoint')
        else:
            self.print("INFO", f'Will create new config at "{user_config_output_path.as_posix()}" using "{entrypoint_path_str}" as entrypoint')

        # remove obsidian_folder_path_str, this is set by the load_paths module
        if "obsidian_folder_path_str" in user_config:
            del user_config["obsidian_folder_path_str"]

        # write new config
        with open(user_config_output_path, "w") as f:
            f.write(yaml.dump(user_config))

        return user_config_output_path.as_posix()

    def test_entrypoint_path_exists(self, entrypoint_path_str):
        entrypoint_path = Path(entrypoint_path_str).resolve()
        entrypoint_abs_path_posix = entrypoint_path.as_posix()
        if not entrypoint_path.exists():
            self.print("ERROR", f"Could not find provided config file at {entrypoint_abs_path_posix}, is the path correct?")
            exit(1)
        return entrypoint_path, entrypoint_abs_path_posix

    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def integrate_save(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass
