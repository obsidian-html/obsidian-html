""" This module is only used to quit execution. Used for testing only """
from ..base_classes import ObsidianHtmlModule


class StopModule(ObsidianHtmlModule):
    @staticmethod
    def requires():
        return tuple()

    @staticmethod
    def provides():
        return tuple()

    @staticmethod
    def alters():
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
