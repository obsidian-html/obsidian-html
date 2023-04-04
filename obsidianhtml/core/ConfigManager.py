import sys
import yaml

from functools import cache
from pathlib import Path

from .. import print_global_help_and_exit
from ..lib import OpenIncludedFile, FindVaultByEntrypoint, get_default_appdir_config_yaml_path

from . import Types as T


class Config:
    config = None
    pb = None

    def __init__(self, pb):
        """
        This init function will do three steps:
        - Merging default config with user config
        - Check that all required values are filled in, all user provided settings are known in default config
        - Setting missing values / Checking for illegal configuration
        """
        self.pb = pb
        self.plugin_settings = {}

    # DITCH
    def resolve_deprecations(self, base_dict, update_dict):
        # if exclude_subfolders is present, copy it to exclude_glob
        if "exclude_subfolders" in update_dict.keys() and isinstance(update_dict["exclude_subfolders"], list):
            self.pb.config["exclude_glob"] = self.pb.config["exclude_subfolders"]

    # # MOVE
    # def load_capabilities_needed(self):
    #     self.capabilities_needed = {}
    #     gc = self.get_config

    #     self.capabilities_needed["directory_tree"] = False
    #     if gc("toggles/features/styling/add_dir_list") or gc("toggles/features/create_index_from_dir_structure/enabled"):
    #         self.capabilities_needed["directory_tree"] = True

    #     self.capabilities_needed["search_data"] = False
    #     if gc("toggles/features/search/enabled") or gc("toggles/features/graph/enabled") or gc("toggles/features/embedded_search/enabled"):
    #         self.capabilities_needed["search_data"] = True

    #     self.capabilities_needed["graph_data"] = False
    #     if gc("toggles/features/rss/enabled") or gc("toggles/features/graph/enabled"):
    #         self.capabilities_needed["graph_data"] = True

    def verbose(self):
        return self.pb.config["toggles"]["verbose_printout"]

    def disable_feature(self, feature_key_name):
        self.pb.config["toggles"]["features"][feature_key_name]["enabled"] = False

    @cache
    def _feature_is_enabled_cached(self, feature_key_name):
        return self.pb.config["toggles"]["features"][feature_key_name]["enabled"]

    def feature_is_enabled(self, feature_key_name, cached=False):
        if cached:
            return self._feature_is_enabled_cached(feature_key_name)
        else:
            return self.pb.config["toggles"]["features"][feature_key_name]["enabled"]

    @cache
    def _get_config_cached(self, path: str):
        return self.get_config(path)

    def get_config(self, path: str):
        keys = [x for x in path.strip().split("/") if x != ""]

        value = self.pb.config
        path = []
        for key in keys:
            path.append(key)
            try:
                value = value[key]
            except KeyError:
                print(path)
                raise Exception(f"INTERNAL ERROR: Config setting '{'/'.join(path)}' not found in config.")
        return value

    # Set config
    def set_config(self, path: str, value):
        keys = [x for x in path.split("/") if x != ""]

        # find key
        ptr = self.pb.config
        ptr_path = []
        for key in keys[:-1]:
            ptr_path.append(key)
            try:
                ptr = ptr[key]
            except KeyError:
                raise Exception(f"INTERNAL ERROR: Config setting '{'/'.join(keys)}' not found in config. (Failed at {ptr_path})")
        ptr[keys[-1]] = value
        return self.get_config(path)

    @cache
    def ShowIcon(self, feature_name):
        return self.pb.gc(f"toggles/features/{feature_name}/enabled") and self.pb.gc(f"toggles/features/{feature_name}/styling/show_icon")

    def LoadIncludedFiles(self):
        # Get html template code.
        if self.pb.gc("toggles/compile_html", cached=True):
            # Every note will become a html page, where the body comes from the note's markdown,
            # and the wrapper code from this template.
            try:
                with open(Path(self.pb.gc("html_template_path_str")).resolve()) as f:
                    html_template = f.read()
            except:
                layout = self.pb.gc("toggles/features/styling/layout")
                html_template = OpenIncludedFile(f"html/layouts/template_{layout}.html")

            if "{content}" not in html_template:
                raise Exception("The provided html template does not contain the string `{content}`. This will break its intended use as a template.")
                exit(1)

            self.pb.html_template = html_template

        if self.pb.gc("toggles/features/graph/enabled", cached=True):
            # Get graph template
            self.pb.graph_template = OpenIncludedFile("graph/graph_template.html")

            # Get graph full page template
            self.pb.graph_full_page_template = OpenIncludedFile("graph/graph_full_page.html")

            # Get grapher template code
            self.pb.graphers = []
            for grapher in self.pb.gc("toggles/features/graph/templates", cached=True):
                gid = grapher["id"]

                # get contents of the file
                if grapher["path"].startswith("builtin<"):
                    grapher["contents"] = OpenIncludedFile(f"graph/default_grapher_{gid}.js")
                else:
                    try:
                        with open(Path(grapher["path"]).resolve()) as f:
                            grapher["contents"] = f.read()
                    except:
                        raise Exception(f"Could not open user provided grapher file with path {grapher['path']}")

                self.pb.graphers.append(grapher)

    def load_embedded_titles_plugin(self):
        """
        There are two options for embedded titles: the recent built-in system, or the older embedded titles plugin.
        """
        pb = self.pb

        # Do nothing if embedded_note_titles are not globally enabled
        if not pb.gc("toggles/features/embedded_note_titles/enabled", cached=True):
            pb.ConfigManager.capabilities_needed["embedded_note_titles"] = False
            if pb.gc("toggles/verbose_printout", cached=True):
                print("\t" * (1), "html: embedded note titles are disabled in config")
            return
        else:
            pb.ConfigManager.capabilities_needed["embedded_note_titles"] = True
            self.plugin_settings["embedded_note_titles"] = {}
            if pb.gc("toggles/verbose_printout", cached=True):
                print("\t" * (1), "html: embedded note titles are enabled in config")

    def check_required_values_filled_in(self, config, path="", match_str="<REQUIRED_INPUT>"):
        def rec(cfgobj, config, path="", match_str="<REQUIRED_INPUT>"):
            helptext = "\n\nTip: Run obsidianhtml -gc to see all configurable keys and their default values.\n"

            for k, v in config.items():
                key_path = "/".join(x for x in (path, k) if x != "")

                if isinstance(v, dict):
                    rec(cfgobj, config[k], path=key_path)

                if v == match_str:
                    if check_required_value_is_required(cfgobj, key_path):
                        raise Exception(f'\n\tKey "{key_path}" is required. {helptext}')
                    else:
                        config[k] = ""

        rec(self, config, path, match_str)


def check_required_value_is_required(cfgobj, key_path):
    if key_path == "obsidian_entrypoint_path_str":
        return cfgobj.get_config("toggles/compile_md")
    return True


def MergeDictRecurse(base_dict, update_dict, path=""):
    helptext = "\n\nTip: Run obsidianhtml -gc to see all configurable keys and their default values.\n"

    def check_leaf(key_path, val):
        if val == "<REMOVED>":
            raise Exception(
                f"\n\tThe setting {key_path} has been removed. Please remove it from your settings file. See https://obsidian-html.github.io/Configurations/Deprecated%20Configurations/Deprecated%20Configurations.html for more information."
            )
        elif val == "<DEPRECATED>":
            print(
                f"DEPRECATION WARNING: The setting {key_path} is deprecated. See https://obsidian-html.github.io/Configurations/Deprecated%20Configurations/Deprecated%20Configurations.html for more information."
            )
            return False
        return True

    for k, v in update_dict.items():
        key_path = "/".join(x for x in (path, k) if x != "")

        # every configured key should be known in base config, otherwise this might suggest a typo/other error
        if k not in base_dict.keys():
            raise Exception(f'\n\tThe configured key "{key_path}" is unknown. Check for typos/indentation. {helptext}')

        # don't overwrite a dict in the base config with a string, or something else
        # in general, we don't expect types to change
        if type(base_dict[k]) != type(v):
            if check_leaf(key_path, base_dict[k]):
                raise Exception(f'\n\tThe value of key "{key_path}" is expected to be of type {type(base_dict[k])}, but is of type {type(v)}. {helptext}')

        # dict match -> recurse
        if isinstance(base_dict[k], dict) and isinstance(v, dict):
            base_dict[k] = MergeDictRecurse(base_dict[k], update_dict[k], path=key_path)
            continue

        # other cases -> copy over
        if isinstance(update_dict[k], list):
            base_dict[k] = v.copy()
        else:
            check_leaf(key_path, base_dict[k])
            base_dict[k] = v

    return base_dict.copy()


def find_user_config_yaml_path(config_yaml_location) -> T.OSAbsolutePosx:
    """This function finds the correct path to load the user config from. It has these options: user provided path (-i path/config.yml), default location, ..."""
    input_yml_path_str = ""

    # Use given value
    if config_yaml_location != "":
        input_yml_path_str = config_yaml_location
    else:
        input_yml_path_str = ""
        for i, v in enumerate(sys.argv):
            if v == "-i":
                if len(sys.argv) < (i + 2):
                    print("No config path given.\n  Use `obsidianhtml convert -i /target/path/to/config.yml` to provide input.")
                    # print_global_help_and_exit(1)
                    exit(1)
                input_yml_path_str = sys.argv[i + 1]
                break

    # Try to find config in default locations
    if input_yml_path_str == "":
        # config.yml in same folder
        if Path("config.yml").exists():
            input_yml_path_str = Path("config.yml").resolve().as_posix()
            print(f"No config provided, using config at {input_yml_path_str} (Default config path)")
    if input_yml_path_str == "":
        # config.yaml in same folder
        if Path("config.yaml").exists():
            input_yml_path_str = Path("config.yaml").resolve().as_posix()
            print(f"No config provided, using config at {input_yml_path_str} (Default config path)")
    if input_yml_path_str == "":
        # config.yml in appdir folder
        appdir_config = Path(get_default_appdir_config_yaml_path())
        if appdir_config.exists():
            input_yml_path_str = appdir_config.as_posix()
            print(f"No config provided, using config at {input_yml_path_str} (Default config path)")

    if input_yml_path_str == "":
        print("No config path given, and none found in default locations.\n  Use `obsidianhtml convert -i /target/path/to/config.yml` to provide input.")
        exit(1)

    return input_yml_path_str
