import os
import yaml
import json

from abc import ABC, abstractmethod
from functools import cache

from ..lib import verbose_enough


class ObsidianHtmlModule(ABC):
    def __init__(self, module_data_fpps, module_name, persistent=False):
        self.set_module_data_folder_path(module_data_fpps)

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
    def run(self, module_data_fpps):
        """Single entrypoint that will be called when it is time for the module to do its thing"""
        print("I am useless! Overwrite me!")

    @property
    def obs_config(self):
        content = self.read("config.yml", allow_absent=True)
        if content != "":
            return yaml.safe_load(content)
        content = self.read("user_config.yml", allow_absent=True)
        if content != "":
            return yaml.safe_load(content)

        raise Exception("Could not load config file")

    @property
    @cache
    def verbosity(self):
        return self.obs_config["verbosity"]

    def print(self, level, msg, force=False):
        if not force and not verbose_enough(level, self.verbosity):
            return

        print(f"[{level.upper():^7}] * {msg}")

    def allow_post_module(self, meta_module):
        """Return True if post module is allowed to run after this one, else return False"""
        return True

    def path(self, rel_path_str_posix):
        """Returns the path of a resource"""
        if rel_path_str_posix[0] == "/":
            rel_path_str_posix = rel_path_str_posix[1:]
        return self.module_data_fpps + "/" + rel_path_str_posix

    def read(self, resource_rel_path, allow_absent=False, asjson=False, asyaml=False):
        path = self.path(resource_rel_path)

        # test if file exists
        if not os.path.isfile(path):
            if not allow_absent:
                raise Exception("Module execution error: Tried to read non-existent resource {path}. Use allow_absent=True if empty string should be returned.")
            else:
                return ""

        with open(self.path(resource_rel_path), "r") as f:
            contents = f.read()
        if asjson:
            return json.loads(contents)
        if asyaml:
            return yaml.safe_load(contents)
        return contents

    def write(self, resource_rel_path, contents, asjson=False, asyaml=False):
        if asjson:

            class class_encoder(json.JSONEncoder):
                def default(self, o):
                    return o.__name__

            contents = json.dumps(contents, indent=2, cls=class_encoder)

        if asyaml:
            contents = yaml.dump(contents)

        with open(self.path(resource_rel_path), "w", encoding="utf-8") as f:
            return f.write(contents)

    def set_module_data_folder_path(self, module_data_folder_path):
        if module_data_folder_path[-1] == "/":
            self.module_data_fpps = module_data_folder_path[:-1]
        else:
            self.module_data_fpps = module_data_folder_path

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


class ObsidianHtmlPostModule(ABC):
    def __init__(self, module_data_fpps, module_name):
        self.module_data_fpps = module_data_fpps

        self._module_class_name = self.__class__.__name__
        self.module_name = module_name
        self.test_module_validity()

    @property
    @abstractmethod
    def provides(self):
        """List of the relative paths of module output files that are created/altered by this module"""
        pass

    @abstractmethod
    def run(self, module_data_fpps, module, result):
        """Single entrypoint that will be called when it is time for the module to do its thing"""
        print("I am useless! Overwrite me!")

    def test_module_validity(self):
        """Tests whether the custom module follows the rules"""
        pass
