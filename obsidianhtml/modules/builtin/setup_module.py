"""
This module will do three seemingly unrelated actions:
- Parse the sys.argv arguments
- Load the user_config.yml path
- Create the module_data folder

This is because of bootstrapping issues, where we depend on the module_data folder,
but don't know where it should go until we have the user config file, and we don't
know where to find the user config file until we have parsed the sys.argv

self.print commands will be cached until we know the verbosity, and then printed.
"""

import sys
import os
import json
import yaml
import uuid
import shutil

from pathlib import Path

from ..base_classes import ObsidianHtmlModule
from ...lib import OpenIncludedFile, MergeDictRecurse, get_arguments_dict
from ...controller.Config import get_config_by_alias


class SetupModule(ObsidianHtmlModule):
    """
    This module will create the arguments.yml file based on the given sysargs.
    """

    @property
    def requires(self):
        return tuple()

    @property
    def provides(self):
        return tuple(["config.yml", "user_config.yml", "arguments.yml", "guid.txt"])

    @property
    def alters(self):
        return tuple()

    def cached_print(self, level, msg):
        if not hasattr(self, "print_cache"):
            self.print_cache = []
        self.print_cache.append((level, msg))

    def printout_cache(self, force=False):
        """Before we have the verbosity information we write prints to a cache, this function prints this cache when the verbosity information is known"""
        if hasattr(self, "print_cache"):
            for level, msg in self.print_cache:
                self.print(level, msg, force=force)

    # --- get user config file path
    def get_user_config_path(self, arguments):
        # see if command is ["convert", "<alias>"]
        if "command" in arguments and isinstance(arguments["command"], list) and len(arguments["command"]) == 2:
            alias = arguments["command"][1]
            config_listing = get_config_by_alias(alias)
            if config_listing is None:
                exit(1)
                
            self.cached_print("INFO", f'Using config file: {config_listing["file"]}')
            return config_listing["file"]

        # try path that was given via sys.argv:
        if os.path.isfile(arguments["config_path"]):
            return arguments["config_path"]

        # Try "config.yml", as per https://github.com/obsidian-html/obsidian-html/issues/57
        if os.path.isfile("config.yml"):
            self.cached_print("info", f"No config provided, using ./config.yml (Default config path)")
            return "config.yml"
        if os.path.isfile("config.yaml"):
            self.cached_print("info", f"No config provided, using ./config.yaml (Default config path)")
            return "config.yaml"

        # Try appdir
        from ...lib import get_default_appdir_config_yaml_path

        input_yml_path_str = get_default_appdir_config_yaml_path().as_posix()
        if os.path.isfile(input_yml_path_str):
            self.cached_print("info", f"No config provided, using config at {input_yml_path_str} (Default config path)")
            return input_yml_path_str

        # no valid config found, caller should handle this
        return None

    def accept(self, module_data_folder=None):
        """This function is run before run(), if it returns False, then the module run is skipped entirely. Any other value will be accepted"""
        return

    # --- main function
    def run(self):
        # parse sys.argv and create arguments dict
        arguments = get_arguments_dict()

        # get path to user_config (if exists, otherwise None)
        arguments["config_path"] = self.get_user_config_path(arguments)

        # entrypoint provided, build/edit user_config
        if "-f" in arguments["literals"].keys():
            from .apply_cmdline_arguments import ApplyCommandlineArgumentsModule
            from ..controller import instantiate_module

            apply_cmdline_arguments_module = instantiate_module(
                module_class=ApplyCommandlineArgumentsModule,
                module_name="apply_cmdline_arguments",
                instantiated_modules=None,
                persistent=False,
                module_data_folder=None,
                verbosity="info",
            )
            arguments["config_path"] = apply_cmdline_arguments_module.run(arguments)

        else:
            if arguments["config_path"] is None:
                self.cached_print(
                    "ERROR",
                    "400: No config path given, and none found in default locations.\n  Use `obsidianhtml convert -i /target/path/to/config.yml` to provide input.",
                )
                self.printout_cache(force=True)
                exit(1)

        self.store("arguments", arguments)


        # get contents of the user config, default_config, and merge them to derive the final config file
        with open(arguments["config_path"], "r") as f:
            user_config_yaml = f.read()
        user_config = yaml.safe_load(user_config_yaml)

        default_config = yaml.safe_load(OpenIncludedFile("defaults_config.yml"))
        config = self.store("config", MergeDictRecurse(default_config, user_config))

        # set module data folder so that we can write output
        if "module_data_folder" not in config:
            self.printout_cache(force=True)
            raise Exception("Config does not contain key 'module_data_folder', which is required")
        self.set_module_data_folder_path(config["module_data_folder"])

        # ensure module data folder exists
        module_data_folder = Path(self.module_data_folder)
        if module_data_folder.exists():
            shutil.rmtree(module_data_folder)
        module_data_folder.mkdir(parents=True, exist_ok=True)

        # write guid.txt, this contains the guid for this run, which can be used to target 
        # files created by a previous run
        with open(self.module_data_folder+"/guid.txt", "w") as f:
            f.write(str(uuid.uuid4()))

        # write config files to module data folder - now we have access to info such as verbosity
        self.modfile("config.yml", config).to_yaml().write()
        self.modfile("user_config.yml", user_config).to_yaml().write()
        self.modfile("arguments.yml", arguments).to_yaml().write()

        # print cached lines now that we know what to print and what not
        self.printout_cache()

        # return module data folder so that the rest of the program knows where to find the info.
        return self.module_data_folder

    def integrate_load(self, pb):
        pass

    def integrate_save(self, pb):
        pb.arguments = self.retrieve("arguments")
        if "verbose" in pb.arguments:
            pb.verbose = pb.arguments["verbose"]
        pb.module_data_folder = self.module_data_folder
