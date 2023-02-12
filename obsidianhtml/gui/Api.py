from .WindowManager import WindowManager
from .Ledger import Ledger
from .ConfigChecker import ConfigChecker
from .lib import open_dialog

from pathlib import Path


class Api:
    def __init__(self):
        self.wm = WindowManager(self)
        self.ledger = Ledger()
        self.config_checker = ConfigChecker(self)

    def get_window(self, args):
        return self.wm.windows[args["window_id"]]["window"]

    def call(self, args):
        a = args["action"]
        if a == "action/get_vault_path":
            return self.get_vault_path(args)
        elif a == "action/get_entrypoint_path":
            return self.get_entrypoint_path(args)
        else:
            print(f"Action path {a} unknown.")
            raise Exception(f"Action path {a} unknown.")

    def get_vault_path(self, args):
        # Get current value
        current_vault_path = self.ledger.get("vault_path")

        # Let user pick value
        picked_vault_path = open_dialog(self.get_window(args), mode="open_folder")

        if picked_vault_path is None:
            vault_path = current_vault_path
        else:
            vault_path = picked_vault_path

        # Store (new) value
        self.ledger.set_value("vault_path", vault_path)

        if not vault_path:
            args["message"] = "None selected"
            args["code"] = 0
            return args

        # Set entrypoint to none if not in new vault
        if not Path(self.ledger.get("entrypoint_path")).is_relative_to(vault_path):
            self.ledger.set_value("entrypoint_path", "")

        args["message"] = f"{vault_path}"
        args["code"] = 200
        return args

    def get_entrypoint_path(self, args):
        vault_path = self.ledger.get("vault_path")
        if not vault_path:
            args["message"] = "First set the vault path"
            args["code"] = 405
            return args

        # Get current value
        current_entrypoint_path = self.ledger.get("entrypoint_path")

        # Let user pick a (new) value
        picked_entrypoint_path = open_dialog(self.get_window(args), directory=vault_path, file_types=("Notes (*.md)",))

        if picked_entrypoint_path is None:
            entrypoint_path = current_entrypoint_path
        else:
            entrypoint_path = picked_entrypoint_path

        # store
        self.ledger.set_value("entrypoint_path", entrypoint_path)

        # return blank if nothing selected
        if not entrypoint_path:
            args["message"] = "None selected"
            args["code"] = 0
            return args

        # Test if valid
        if not Path(entrypoint_path).is_relative_to(vault_path):
            self.ledger.set_value("entrypoint_path", "")  # nullify previous value
            args["message"] = "Entrypoint should be located in the vault"
            args["code"] = 405
            return args

        # all checks out
        args["message"] = f"{entrypoint_path}"
        args["code"] = 200
        return args

    def read_ledger(self, load_list):
        for req in load_list:
            req["value"] = self.ledger.get(req["id"])

        return {"message": "Something failed while fetching data", "data": load_list}

    def LaunchWindow(self, window_id, window_title, html_path, parent_window_id=None):
        # html_path: relative to obsidianhtml/src/installer/dist/
        self.wm.LaunchWindow(window_id, window_title, html_path, parent_window_id)
