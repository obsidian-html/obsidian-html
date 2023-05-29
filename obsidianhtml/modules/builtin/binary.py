import json
from pathlib import Path

from ..base_classes import ObsidianHtmlModule

class BinaryModule(ObsidianHtmlModule):
    """Used to run any binary as a module"""
    @property
    def requires(self):
        return tuple(["config.yml"])

    @property
    def provides(self):
        return tuple(["paths.json"])

    @property
    def alters(self):
        return tuple()
        
    def accept(self, module_data_folder):
        """ Returns True if module should be run, otherwise false"""
        #self.print("Debug", f"Running binary module ACCEPT ({self.binary_path})")
        res = self.run_binary(["accept", self.module_data_folder_abs])
        return res["result"]

    def run(self):
        res = self.run_binary(["run", self.module_data_folder_abs])
        return res["result"]

    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def integrate_save(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass