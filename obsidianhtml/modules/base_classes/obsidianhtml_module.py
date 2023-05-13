import os
import yaml
import json
import inspect

from abc import ABC, abstractmethod
from functools import cache
from pathlib import Path
from datetime import datetime

from ..lib import verbose_enough, hash_wrap
from ...lib import formatted_print
from .. import handlers


class ResourceAccessLog:
    def __init__(self):
        self.log = []

    def add(self, resource_rel_path):
        self.log.append(
            {
                "datetime": datetime.now().isoformat(),
                "resource_rel_path": resource_rel_path,
            }
        )

    def listing(self):
        return [x["resource_rel_path"] for x in self.log]


class ObsidianHtmlModule(ABC):
    def __init__(self, module_data_folder, module_name, persistent=None):
        # overwrites
        self.__verbosity__overwrite__ = None

        # set values
        self.set_module_data_folder_path(module_data_folder)

        self.module_class_name = self.__class__.__name__
        self.module_name = module_name
        self.test_module_validity()

        self.persistent = persistent
        self.states = {}
        self.states["cancelled_run"] = False

        # shortcuts
        self.verbose_enough = verbose_enough

        # init
        self._stash = {}  # see self.stash()

        # records
        self.written_files = ResourceAccessLog()
        self.read_files = ResourceAccessLog()
        self.stored_keys = ResourceAccessLog()
        self.retrieved_keys = ResourceAccessLog()

        # module config
        self.mod_config = {}
        self.define_mod_config_defaults()
        if self.module_data_folder is not None:
            self.try_load_mod_config()

    @property
    def nametag(self):
        return f'{self.module_name} ({self.module_class_name})'

    def define_mod_config_defaults(self):
        pass

    def try_load_mod_config(self):
        cfg = self.modfile("config.yml", allow_absent=True).read(sneak=True).from_yaml()
        
        if cfg is None:
            return

        if self.module_name not in cfg["module_config"].keys():
            return

        mcfg = cfg["module_config"][self.module_name]
        if not isinstance(mcfg, dict):
            raise Exception(f'Expected type dict for config key module_config/{self.module_name}, but got {type(mcfg)}.')
        
        for key, item in mcfg.items():
            if key not in self.mod_config:
                raise Exception(f'Module config key "{key}" is unknown to module {self.nametag}')
            self.mod_config[key]["value"] = item["value"]

    def value_of(self, mod_config_key):
        if mod_config_key not in self.mod_config:
            raise Exception(f'Value of module config with key {mod_config_key} requested, but not set, in module {self.nametag}')
        return self.mod_config[mod_config_key]["value"]

    @property
    @abstractmethod
    def requires(self):
        """List of the relative paths of module output files that are used as input to this module"""
        pass

    @property
    @abstractmethod
    def provides(self):
        """List of the relative paths of module output files that are created/altered by this module"""
        pass

    @property
    @abstractmethod
    def alters(self):
        """List of strings denoting which targets are altered by this module"""
        pass

    @abstractmethod
    def accept(self, module_data_folder):
        """This function is run before run(), if it returns False, then the module run is skipped entirely. Any other value will be accepted"""
        return

    @abstractmethod
    def run(self, module_data_folder):
        """Single entrypoint that will be called when it is time for the module to do its thing"""
        print("I am useless! Overwrite me!")

    def _integrate_ensure_module_data_folder(self):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        Path(self.module_data_folder).mkdir(exist_ok=True)

    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        raise Exception(f"integrate_load not implemented for module class {self.module_class_name}")

    def integrate_save(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        raise Exception(f"integrate_save not implemented for module class {self.module_class_name}")

    @property
    @cache
    def config(self):
        """Read the config.yml file and load the yaml content so that we can easily use the values in the module"""
        cfg = self.modfile("config.yml", allow_absent=True).read().from_yaml()
        if cfg is not None:
            return cfg

        cfg = self.modfile("user_config.yml", allow_absent=True).read().from_yaml()
        if cfg is not None:
            return cfg

        raise Exception("Could not load config file")

    def gc(self, path: str, config=None, cached=False):
        """This function makes is easier to get deeply nested config values by allowing path/to/nested/value instead of ["path"]["to"]["nested"]["value"].
        It also handles errors in case of key not found."""
        if config is None:
            config = self.config
        if cached:
            return handlers.config.get_config_cached(config, path)
        return handlers.config.get_config(config, path)

    @property
    @cache
    def verbosity(self):
        if self.__verbosity__overwrite__ is not None:
            return self.__verbosity__overwrite__
        return self.config["verbosity"]

    def path(self, rel_path_str_posix):
        """Returns the path of a resource"""
        if rel_path_str_posix[0] == "/":
            rel_path_str_posix = rel_path_str_posix[1:]
        return self.module_data_folder + "/" + rel_path_str_posix

    def modfile(
        self,
        resource_rel_path,
        contents="",
        encoding="utf-8",
        allow_absent=False,
    ):
        """Returns an object through which module files can be read and written in a standardized way"""
        return handlers.file.File(
            resource_rel_path=resource_rel_path,
            path=self.path(resource_rel_path),
            contents=contents,
            encoding=encoding,
            allow_absent=allow_absent,
            module=self,
        )

    def print(self, level, msg, force=False):
        """Print (or not print) based on verbosity"""
        if not force and not verbose_enough(level, self.verbosity):
            return

        formatted_print(level, msg)

    def store(self, key, value, overwrite=False):
        """Saves the value under the key for later use in the module"""
        if overwrite is False and key in self._stash:
            raise Exception(f"Module Validity Error: Value {value} is stored twice, without overwrite being set to true.")

        # log
        if self.persistent:
            resource_name = self.module_name + "(" + self.module_class_name + ")/" + key
            self.stored_keys.add(resource_name)

        # apply
        self._stash[key] = value
        return value

    def retrieve(self, key):
        """Retrievs stored value from the internal stash"""
        # log
        if self.persistent and inspect.stack()[1][3] not in ("integrate_save",):
            resource_name = self.module_name + "(" + self.module_class_name + ")/" + key
            self.retrieved_keys.add(resource_name)

        # return
        return self._stash[key]

    def allow_post_module(self, meta_module):
        """Return True if post module is allowed to run after this one, else return False"""
        return True

    def set_module_data_folder_path(self, module_data_folder_path):
        """Ensures that the module_data_folder is not prefixed with a '/'"""
        if module_data_folder_path is None:
            self.module_data_folder = module_data_folder_path
            return
        if module_data_folder_path[-1] == "/":
            self.module_data_folder = module_data_folder_path[:-1]
        else:
            self.module_data_folder = module_data_folder_path

    def test_module_validity(self):
        """Tests whether the custom module follows the rules"""
        failed = False
        errors = []

        def log_error(message):
            nonlocal failed, errors
            failed = True
            errors.append(message)

        # property types should be correct
        if not isinstance(self.requires, tuple):
            log_error("Module Validity Error: self.requires() should return a tuple")
        if not isinstance(self.provides, tuple):
            log_error("Module Validity Error: self.provides() should return a tuple")
        if not isinstance(self.alters, tuple):
            log_error("Module Validity Error: self.alters() should return a tuple")
        else:
            allowed_alters_values = (
                "md_notes",
                "html_notes",
                "vault_notes",
                "md_misc",
                "html_misc",
                "vault_misc",
            )
            for val in self.alters:
                if val not in allowed_alters_values:
                    log_error(f"Module Validity Error: value {val} in self.alters is not allowed. Allowed values: {allowed_alters_values}")

        if failed:
            raise Exception("\n- " + "\n- ".join(errors))
