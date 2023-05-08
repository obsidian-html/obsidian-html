from ..base_classes import ObsidianHtmlModule

import yaml
from pathlib import Path


class ProcessConfigModule(ObsidianHtmlModule):
    """
    After merging the user_config with the default_config to arrive at the config.yml, we need to do some checks,
    and derrive values from the config to make decision making easier later on.
    """

    @property
    def requires(self):
        return tuple(["config.yml", "arguments.yml"])

    @property
    def provides(self):
        return tuple(["config.yml", "capabilities.json"])

    @property
    def alters(self):
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
        config = self.config

        # check if config is valid
        self.check_required_values_filled_in(config)

        # mutate config
        arguments = self.modfile("arguments.yml").read().from_yaml()
        self.overwrite_values(config, arguments)

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
