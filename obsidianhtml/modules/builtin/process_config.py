from ..base_classes import ObsidianHtmlModule

import yaml
import json
from pathlib import Path


class ProcessConfigModule(ObsidianHtmlModule):
    """
    After merging the user_config with the default_config to arrive at the config.yml, we need to do some checks,
    and derrive values from the config to make decision making easier later on.
    """

    @staticmethod
    def requires():
        return tuple(["config.yml", "arguments.yml"])

    @staticmethod
    def provides():
        return tuple(["config.yml", "capabilities.json"])

    @staticmethod
    def alters():
        return tuple()

    # --- check user config
    def check_required_values_filled_in(self, config, path="", match_str="<REQUIRED_INPUT>"):
        def rec(config, path="", match_str="<REQUIRED_INPUT>"):
            helptext = "\n\nTip: Run obsidianhtml -gc to see all configurable keys and their default values.\n"

            for k, v in config.items():
                key_path = "/".join(x for x in (path, k) if x != "")

                if isinstance(v, dict):
                    rec(config[k], path=key_path)

                if v == match_str:
                    if self.check_required_value_is_required(config, key_path):
                        raise Exception(f'\n\tKey "{key_path}" is required. {helptext}')
                    else:
                        config[k] = ""

        rec(config, path, match_str)

    def check_required_value_is_required(self, config, key_path):
        if key_path == "obsidian_entrypoint_path_str":
            return self.gc("toggles/compile_md", config=config)
        return True

    def overwrite_values(self, config, arguments):
        # (If -v is passed in, __init__.py will set self.verbose to true)
        if "verbose" in arguments:
            config["toggles"]["verbose_printout"] = arguments["verbose"]

        # Set toggles/no_tabs
        layout = config["toggles"]["features"]["styling"]["layout"]
        if layout == "tabs":
            config["toggles"]["no_tabs"] = False
        else:
            config["toggles"]["no_tabs"] = True

        # Set main css file
        config["_css_file"] = f"main_{layout}.css"

    def load_capabilities_needed(self):
        capabilities_needed = {}
        gc = self.gc

        capabilities_needed["directory_tree"] = False
        if gc("toggles/features/styling/add_dir_list") or gc("toggles/features/create_index_from_dir_structure/enabled"):
            capabilities_needed["directory_tree"] = True

        capabilities_needed["search_data"] = False
        if gc("toggles/features/search/enabled") or gc("toggles/features/graph/enabled") or gc("toggles/features/embedded_search/enabled"):
            capabilities_needed["search_data"] = True

        capabilities_needed["graph_data"] = False
        if gc("toggles/features/rss/enabled") or gc("toggles/features/graph/enabled"):
            capabilities_needed["graph_data"] = True

        capabilities_needed["embedded_note_titles"] = False
        if gc("toggles/features/embedded_note_titles/enabled"):
            capabilities_needed["embedded_note_titles"] = True

        return capabilities_needed

    def accept(self, module_data_folder):
        """This function is run before run(), if it returns False, then the module run is skipped entirely. Any other value will be accepted"""
        return

    def run(self):
        config = self.config.unwrap()

        # check if config is valid
        self.check_required_values_filled_in(config)

        # mutate config
        arguments = self.modfile("arguments.yml").read().from_yaml()
        self.overwrite_values(config, arguments)

        # check that entrypoint exists
        if config["toggles"]["compile_md"]:
            entrypoint = Path(config["obsidian_entrypoint_path_str"])
            if not entrypoint.exists():
                self.print("ERROR", f"The entrypoint that you configured does not seem to exist. \nCheck that the file {entrypoint} exists before you continue.")
                exit(1)
        else:
            entrypoint = Path(config["md_entrypoint_path_str"])
            if not entrypoint.exists():
                self.print("ERROR", f"The entrypoint that you configured does not seem to exist. \nCheck that the file {entrypoint} exists before you continue.")
                exit(1)

        # Export config
        self.modfile("config.yml", config).to_yaml().write()

        # capabilities_needed.json
        capabilities_needed = self.store("capabilities_needed", self.load_capabilities_needed())
        self.modfile("capabilities.json", capabilities_needed).to_json().write()

    def integrate_load(self, pb):
        pass

    def integrate_save(self, pb):
        pb.config = self.config
        pb.configured_html_prefix = self.config["html_url_prefix"]  # REFACTOR: REPLACE
        pb.capabilities_needed = self.retrieve("capabilities_needed")


class ProcessConfigAutoModule(ObsidianHtmlModule):
    """
    Some values in the config can have value "auto". This module aims to fill in these values.
    """

    @staticmethod
    def requires():
        return tuple(["config.yml", "paths.json"])

    @staticmethod
    def provides():
        return tuple(["config.yml"])

    @staticmethod
    def alters():
        return tuple()

    def strict_line_breaks_auto(self, config, original_obsidian_folder):
        """ 
            When auto is set, it will attempt to read (vault)/.obsidian/app.json, and look for 'strictLineBreaks'.
            If the app.json file is not found, it will default to false (the default in obsidian)
            If the strictLineBreaks key is not found, it will default to false
        """

        # do not execute if value is not auto
        if config["toggles"]["strict_line_breaks"] != "auto":
            return

        # get the value of strictLineBreaks in obsidian vault
        def get_strict_line_value(original_obsidian_folder):
            app_json_path = Path(original_obsidian_folder).joinpath(".obsidian/app.json")
            if not app_json_path.exists():
                return False
            with open(app_json_path, 'r') as f:
                obs_conf = json.loads(f.read())
            if "strictLineBreaks" not in obs_conf.keys():
                return False

            return obs_conf["strictLineBreaks"]

        val = get_strict_line_value(original_obsidian_folder)

        # set value in config
        config["toggles"]["strict_line_breaks"] = val


    def accept(self, module_data_folder):
        """This function is run before run(), if it returns False, then the module run is skipped entirely. Any other value will be accepted"""
        return

    def run(self):
        # read modfiles
        config = self.config.unwrap()
        paths = self.modfile("paths.json").read().from_json()

        # fill in auto values
        self.strict_line_breaks_auto(config, original_obsidian_folder=paths["original_obsidian_folder"])

        # Export config
        self.modfile("config.yml", config).to_yaml().write()


    def integrate_load(self, pb):
        pass

    def integrate_save(self, pb):
        pb.config = self.config
        pb.verbosity = self.config["verbosity"]