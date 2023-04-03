import os
import yaml
import json

from abc import ABC, abstractmethod
from functools import cache
from pathlib import Path

from ..lib import verbose_enough, hash_wrap
from .. import handlers


class ObsidianHtmlModule(ABC):
    def __init__(self, module_data_folder, module_name, persistent=False):
        self.set_module_data_folder_path(module_data_folder)

        self.module_class_name = self.__class__.__name__
        self.module_name = module_name
        self.test_module_validity()

        self.persistent = persistent

        # shortcuts
        self.verbose_enough = verbose_enough

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
    def run(self, module_data_folder):
        """Single entrypoint that will be called when it is time for the module to do its thing"""
        print("I am useless! Overwrite me!")

    def _integrate_ensure_module_data_folder(self):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        Path(self.module_data_folder).mkdir(exist_ok=True)

    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        raise Exception("integrate_load not implemented")

    def integrate_save(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        raise Exception("integrate_save not implemented")

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
        return self.config["verbosity"]

    def path(self, rel_path_str_posix):
        """Returns the path of a resource"""
        if rel_path_str_posix[0] == "/":
            rel_path_str_posix = rel_path_str_posix[1:]
        return self.module_data_folder + "/" + rel_path_str_posix

    def modfile(self, resource_rel_path, contents="", encoding="utf-8", allow_absent=False):
        return handlers.file.File(resource_rel_path=resource_rel_path, path=self.path(resource_rel_path), contents=contents, encoding=encoding, allow_absent=allow_absent, module=self)

    def print(self, level, msg, force=False):
        if not force and not verbose_enough(level, self.verbosity):
            return

        print(f"[{level.upper():^7}] * {msg}")

    def allow_post_module(self, meta_module):
        """Return True if post module is allowed to run after this one, else return False"""
        return True

    def set_module_data_folder_path(self, module_data_folder_path):
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
            allowed_alters_values = ("md_notes", "html_notes", "vault_notes", "md_misc", "html_misc", "vault_misc")
            for val in self.alters:
                if val not in allowed_alters_values:
                    log_error(f"Module Validity Error: value {val} in self.alters is not allowed. Allowed values: {allowed_alters_values}")

        if failed:
            raise Exception("\n- " + "\n- ".join(errors))
