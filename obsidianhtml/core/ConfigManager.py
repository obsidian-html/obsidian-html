import sys
import yaml

from functools import cache
from pathlib import Path

from .. import print_global_help_and_exit
from ..lib import OpenIncludedFile, find_vault_folder_by_entrypoint, get_default_appdir_config_yaml_path

from . import Types as T


class Config:
    config = None
    pb = None

    def __init__(self, pb):
        self.pb = pb

    # DITCH
    def resolve_deprecations(self, base_dict, update_dict):
        # if exclude_subfolders is present, copy it to exclude_glob
        if "exclude_subfolders" in update_dict.keys() and isinstance(update_dict["exclude_subfolders"], list):
            self.pb.config["exclude_glob"] = self.pb.config["exclude_subfolders"]

    def verbose(self):
        return self.pb.config["toggles"]["verbose_printout"]

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
