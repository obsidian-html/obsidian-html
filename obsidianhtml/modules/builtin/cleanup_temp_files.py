import os
from ..base_classes import ObsidianHtmlModule


class CleanupTempFilesModule(ObsidianHtmlModule):
    """
    This module will remove all temporary files after we are done running.
    """

    @staticmethod
    def requires():
        return tuple()

    @staticmethod
    def provides():
        return tuple()

    @staticmethod
    def alters():
        return tuple()

    def allow_post_module(self, meta_module):
        """Return True if post module is allowed to run after this one, else return False"""
        if meta_module.module_class_name in ["ResourceLoggerMetaModule"]:
            return False
        return True

    def accept(self, module_data_folder):
        """This function is run before run(), if it returns False, then the module run is skipped entirely. Any other value will be accepted"""
        return

    def run(self):
        for resource in ["log.resources", "config.yml", "arguments.yml", "paths.json"]:
            path = self.path(resource)
            if os.path.isfile(path):
                self.print("info", f"removing {path}")
                os.remove(path)
