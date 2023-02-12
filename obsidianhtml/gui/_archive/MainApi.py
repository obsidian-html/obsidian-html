from ..lib import OpenIncludedFile
from .lib import open_dialog
from .InstallerApi import InstallerApi

import os
from pathlib import Path

import webview  # pywebview
from appdirs import AppDirs


class Api:
    msg = None
    windows = None
    testval = 0

    # Helper objects
    ledger = None
    config_checker = None

    def __init__(self):
        self.ledger = Ledger()
        self.config_checker = ConfigChecker(self)
        self.windows = {}

    def close(self, window_id):
        self.windows[window_id].destroy()

    def call(self, method_name, args={}):
        print(args)

        def func_not_found(**kwargs):
            return {"message": f"Unknown functon call {method_name}", "code": "500"}

        func = getattr(self, method_name, func_not_found)
        return func(**args)

    def LaunchSetupObsidianHtml(self):
        html = OpenIncludedFile("installer/init.html")

        self.windows["setup_obsidianhtml"] = webview.create_window("Setup ObsidianHtml", html=html, js_api=self)

        return {"message": "setup opened"}

    def LaunchVaultGithubPagesInstaller(self):
        try:
            api = InstallerApi(self)
            html = OpenIncludedFile("installer/gp_installer.html")

            api.windows["self"] = webview.create_window("GithubPages Installer", html=html, js_api=api)
        except Exception as e:
            print(e)

        return {"message": "installer running"}

    def LaunchSettingsOverview(self):
        html = OpenIncludedFile("installer/configurations.html")

        self.windows["configurations"] = webview.create_window("Settings", html=html, js_api=self)

        return {"message": "settings pane opened"}

    def read_ledger(self, request):
        data = {}
        div_ids = request["div_ids"]
        value_ids = request["ids"]

        for i, value_id in enumerate(value_ids):
            value = self.ledger.get(value_id)
            data[value_id] = {"value": value, "div_id": div_ids[i]}

        return {"message": "Something failed while fetching data", "ids": value_ids, "data": data}

    def getVaultPath(self, window_id):
        folder_path = open_dialog(self.windows[window_id], mode="open_folder")

        self.ledger.set_value("vault_path", folder_path)

        if folder_path is None:
            return {"message": "None selected", "code": 0}
        return {"message": f"{folder_path}", "code": 200}

    def getVersion(self):
        stream = os.popen("pip show obsidianhtml")
        output = stream.read()
        response = {"message": output}
        return response

    def temp_SetupGitpages(self):
        api = InstallerApi(self.windows["self"])
        api.OpenWindowSetupGitpage()

        response = {"message": "installer running"}
        return response


class Ledger:
    ledger = None

    def __init__(self):
        self.ledger = {}
        self.ledger["vault_path"] = ""
        self.ledger["entrypoint_path"] = ""
        self.ledger["markdown_folder_path"] = ""
        self.ledger["markdown_entrypoint_path"] = ""
        self.ledger["repo_folder_path"] = ""
        self.ledger["config_folder_path"] = AppDirs("obsidianhtml", "obsidianhtml").user_config_dir

        self.ledger["gitpages_configured"] = False
        self.ledger["test"] = 0

    def get(self, value_id):
        # Get value
        if value_id not in self.ledger.keys():
            raise Exception(f"key {value_id} not present in ledger")

        value = self.ledger[value_id]

        # Set default
        return value

    def set_value(self, id, value):
        if id == "vault_path":
            return self.set_vault_path(value)
        elif id == "entrypoint_path":
            return self.set_entrypoint_path(value)
        elif id == "config_folder_path":
            return self.set_config_folder_path(value)
        elif id == "markdown_folder_path":
            return self.set_markdown_folder_path(value)
        elif id == "markdown_entrypoint_path":
            return self.set_markdown_entrypoint_path(value)
        elif id == "repo_folder_path":
            return self.set_repo_folder_path(value)
        elif id == "gitpages_configured":
            return self.set_gitpages_configured(value)
        else:
            raise Exception(f"id {id} not known (Ledger.set_value())")

    def set_vault_path(self, value):
        self.ledger["vault_path"] = value

    def set_entrypoint_path(self, value):
        self.ledger["entrypoint_path"] = value

    def set_config_folder_path(self, value):
        self.ledger["config_folder_path"] = value

    def set_markdown_folder_path(self, value):
        self.ledger["markdown_folder_path"] = value

    def set_markdown_entrypoint_path(self, value):
        self.ledger["markdown_entrypoint_path"] = value

    def set_gitpages_configured(self, value):
        self.ledger["gitpages_configured"] = value

    def set_repo_folder_path(self, value):
        self.ledger["repo_folder_path"] = value


class ConfigChecker:
    main_api = None
    ledger = None

    def __init__(self, main_api):
        self.main_api = main_api
        self.ledger = main_api.ledger

    def DetermineDefaultConfigFolderPath(self):
        return AppDirs("obsidianhtml", "obsidianhtml")

    def presetConfigPath(self):
        # get configured value
        config_folder_path = self.ledger.get("config_folder_path")

        if config_folder_path == "":
            config_folder_path = self.DetermineDefaultConfigFolderPath()
            self.ledger.set_value("config_folder_path", config_folder_path)

    def presetRepoClonePath(self, repo_name):
        value = self.ledger.get("repo_folder_path")
        if value == "":
            folder = Path.home().as_posix()
            if Path.home().joinpath("git").exists():
                folder = Path.home().joinpath("git").as_posix()
            elif Path.home().joinpath("Git").exists():
                folder = Path.home().joinpath("Git").as_posix()

            self.ledger.set_value("repo_folder_path", Path(folder).joinpath(repo_name).as_posix())
