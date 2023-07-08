import json
from pathlib import Path

from ..base_classes import ObsidianHtmlModule, run_binary


class BinaryModule(ObsidianHtmlModule):
    """Used to run any binary as a module"""

    @staticmethod
    def requires(**kwargs):
        if "binary_path" not in kwargs.keys():
            raise Exception("cannot run static method requires on BinaryModule without binary_path kwarg")
        binary_path = kwargs["binary_path"]

        res = run_binary([binary_path, "requires"])
        return tuple(res)

    @staticmethod
    def provides(**kwargs):
        if "binary_path" not in kwargs.keys():
            raise Exception("cannot run static method provides on BinaryModule without binary_path kwarg")
        binary_path = kwargs["binary_path"]

        res = run_binary([binary_path, "provides"])
        return tuple(res)

    @staticmethod
    def alters(**kwargs):
        if "binary_path" not in kwargs.keys():
            raise Exception("cannot run static method alters on BinaryModule without binary_path kwarg")
        binary_path = kwargs["binary_path"]

        res = run_binary([binary_path, "alters"])
        return tuple(res)

    def accept(self, module_data_folder):
        """Returns True if module should be run, otherwise false"""
        # self.print("Debug", f"Running binary module ACCEPT ({self.binary_path})")
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
