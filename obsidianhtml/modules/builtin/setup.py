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

from .. import ObsidianHtmlModule
from ...lib import OpenIncludedFile
from ...core.ConfigManager import MergeDictRecurse

import sys
import os
import yaml
from pathlib import Path

class SetupModule(ObsidianHtmlModule):
    """
    This module will create the arguments.yml file based on the given sysargs.
    """
    @property
    def requires(self):
        return tuple()
    @property
    def provides(self):
        return tuple(['arguments.yml'])
    @property
    def alters(self):
        return tuple()

    def cached_print(self, level, msg):
        if not hasattr(self, "print_cache"):
            self.print_cache = []
        self.print_cache.append((level, msg))

    def printout_cache(self, force=False):
        if hasattr(self, "print_cache"):
            for level, msg in self.print_cache:
                self.print(level, msg, force=force)

    # --- parse commandline
    def get_arguments_dict(self):
        def determine_command():
            if "-h" in sys.argv or "--help" in sys.argv or "help" in sys.argv:
                return "help"

            if len(sys.argv) < 2 or sys.argv[1][0] == "-":
                self.cached_print('deprecation', 'DEPRECATION WARNING: You did not pass in a command. Assuming you meant "convert". Starting version 4.0.0 providing a command will become mandatory.')
                return "convert"
            else:
                command = sys.argv[1]

        def determine_config_path():
            for i, v in enumerate(sys.argv):
                if v == "-i":
                    if len(sys.argv) < (i + 2):
                        self.cached_print("error", "No config path given.\n  Use `obsidianhtml convert -i /target/path/to/config.yml` to provide input.")
                        self.printout_cache(force=True)
                        exit(1)
                    return sys.argv[i + 1]
            return ""

        arguments = {}
        arguments["command"] = determine_command()
        arguments["config_path"] = determine_config_path()

        return arguments

    def write_arguments_yaml(self, arguments):
        self.write('arguments.yml', arguments, asyaml=True)

    # --- get user config file path
    def get_user_config_path(self, arguments):
        # try path that was given via sys.argv:
        if os.path.isfile(arguments['config_path']):
            return arguments['config_path']

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

        self.cached_print("error", "No config path given, and none found in default locations.\n  Use `obsidianhtml convert -i /target/path/to/config.yml` to provide input.")
        self.printout_cache(force=True)
        exit(1)
    
    def run(self):
        # parse sys.argv and create arguments dict
        arguments = self.get_arguments_dict()

        # get path to user_config
        user_config_path = self.get_user_config_path(arguments)

        # get contents of the user config, default_config, and merge them to derive the final config file
        with open(user_config_path, 'r') as f:
            user_config_yaml = f.read()
        user_config = yaml.safe_load(user_config_yaml)

        default_config = yaml.safe_load(OpenIncludedFile("defaults_config.yml"))
        config = MergeDictRecurse(default_config, user_config)

        # set module data folder so that we can write output
        if "module_data_folder" not in config:
            self.printout_cache(force=True)
            raise Exception("Config does not contain key 'module_data_folder', which is required")
        self.set_module_data_folder_path(config["module_data_folder"])

        # ensure module data folder exists
        Path(self.module_data_fpps).mkdir(exist_ok=True)

        # write config files to module data folder - now we have access to info such as verbosity
        self.write('config.yml', config, asyaml=True)
        self.write('user_config.yml', user_config, asyaml=True)
        
        # print cached lines now that we know what to print and what not
        self.printout_cache()

        # output the arguments.yml now that we know where to write them to
        self.write_arguments_yaml(arguments)

        # return module data folder so that the rest of the program knows where to find the info.
        return self.module_data_fpps



