""" This module is only used to quit execution. Used for testing only """
from ..base_classes import ObsidianHtmlModule

class StopModule(ObsidianHtmlModule):
    @property
    def requires(self):
        return tuple(["config.yml"])

    @property
    def provides(self):
        return tuple(["paths.json"])

    @property
    def alters(self):
        return tuple()

    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def integrate_save(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def accept(self, module_data_folder):
        return True
        
    def run(self):
        exit()