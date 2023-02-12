from appdirs import AppDirs

import yaml
from pathlib import Path


class Ledger:
    ledger = None

    def __init__(self):
        self.ledger = {}
        self.save_keys = {
            "vault_path": {"type": Path, "default": ""},
            "entrypoint_path": {"type": Path, "default": ""},
            "markdown_folder_path": {"type": Path, "default": ""},
            "markdown_entrypoint_path": {"type": Path, "default": ""},
            "repo_folder_path": {"type": Path, "default": ""},
            "gitpages_configured": {"type": bool, "default": False},
        }

        self.ledger["config_folder_path"] = Path(AppDirs("obsidianhtml", "obsidianhtml").user_config_dir)
        self.ledger["gui_config_file_path"] = self.ledger["config_folder_path"].joinpath("gui_conf.yml")

        if Path(self.ledger["gui_config_file_path"]).exists():
            self.read_from_file()

    def read_from_file(self):
        """Read config from file and build ledger using that information"""
        # get saved config
        conf = None

        if self.ledger["gui_config_file_path"].exists():
            with open(self.ledger["gui_config_file_path"], "r", encoding="utf-8") as f:
                conf = yaml.safe_load(f.read())

        if conf is None:
            conf = {}

        # load values into ledger
        for key in self.save_keys:
            # get either saved or default value
            if key not in conf.keys():
                # no value found; get default value as defined in save_keys
                val = self.save_keys[key]["default"]
            else:
                # value found; convert where necessary
                val = conf[key]
                if self.save_keys[key]["type"] == Path:
                    if val is None or val == "":
                        val = None
                    else:
                        val = Path(val)

            # write value to ledger
            self.ledger[key] = val

    def write_to_file(self):
        # compile dict to save
        conf = {}
        for key in self.save_keys:
            conf[key] = self.ledger[key]

        with open(self.ledger["gui_config_file_path"], "w", encoding="utf-8") as f:
            f.write(self.stringify_config(conf))

        print("saved config to", self.ledger["gui_config_file_path"])

    def stringify_config(self, config):
        for key in config:
            if isinstance(config[key], Path):
                config[key] = config[key].resolve().as_posix()
            if config[key] is None:
                config[key] = ""

        return yaml.dump(config)

    def get(self, value_id):
        if value_id not in self.ledger.keys():
            raise Exception(f"key {value_id} not present in ledger")

        val = self.ledger[value_id]
        if isinstance(val, Path):
            return val.resolve().as_posix()
        return val

    def set_value(self, id, value):
        if id not in self.ledger.keys():
            raise Exception(f"id {id} not known (Ledger.set_value())")

        if isinstance(value, Path):
            value = value.resolve().as_posix()

        self.ledger[id] = value
        self.write_to_file()
