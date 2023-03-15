from .. import ObsidianHtmlModule

import sys
import os


class PutUserConfig(ObsidianHtmlModule):
    """
    This module will get the user config file and place it in the module_data folder.
    If the value listed in arguments.yml:/config_path is not valid, it will try common other paths, such as the appdir
    It will fail if no config file is located.

    Due to bootstrapping issues, this module will create the module_data folder as well.
    Printing will not happen unless
    """

    @property
    def requires(self):
        return tuple(["arguments.yml"])

    @property
    def provides(self):
        return tuple(["user_config.yml", "arguments.yml"])

    @property
    def alters(self):
        return tuple()

    def run(self):
        self.print("info", f"running {self.module_name}")

        # get value from arguments.yml
        arguments = self.read("arguments.yml", asyaml=True)

        def validate_config_path_and_copy(src_path):
            if os.path.isfile(src_path):
                # copy file contents over
                dst_path = self.path("user_config.yml")
                with open(src_path, "r") as s:
                    contents = s.read()
                with open(dst_path, "w") as d:
                    d.write(contents)
                return True
            return False

        # try path that was given via sys.argv:
        if validate_config_path_and_copy(arguments["config_path"]):
            return

        # Try "config.yml", as per https://github.com/obsidian-html/obsidian-html/issues/57
        if validate_config_path_and_copy("config.yml"):
            self.print("info", f"No config provided, using ./config.yml (Default config path)")
            return
        if validate_config_path_and_copy("config.yaml"):
            self.print("info", f"No config provided, using ./config.yaml (Default config path)")
            return

        # Try appdir
        from ...lib import get_default_appdir_config_yaml_path

        input_yml_path_str = get_default_appdir_config_yaml_path().as_posix()
        if validate_config_path_and_copy(input_yml_path_str):
            self.print("info", f"No config provided, using config at {input_yml_path_str} (Default config path)")
            return

        self.print("error", "No config path given, and none found in default locations.\n  Use `obsidianhtml convert -i /target/path/to/config.yml` to provide input.")
        exit(1)
