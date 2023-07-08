from .lib import open_dialog
from ..lib import OpenIncludedFile

from pathlib import Path
import webbrowser
import requests

import os
import webview  # pywebview

from subprocess import Popen, PIPE


class InstallerApi:
    main_api = None
    config_checker = None
    ledger = None

    windows = {}

    obsidian_vault_path = None
    repo_name = ""
    repo_url = ""
    git_username = ""
    git_email = ""

    def __init__(self, main_api):
        self.main_api = main_api
        self.ledger = main_api.ledger
        self.config_checker = main_api.config_checker

        self.windows = {"parent": main_api.windows["self"], "self": None, "setup_gitpages": None}

    def close(self, window_id):
        self.windows[window_id].destroy()

    def call(self, method_name, args={}):
        def func_not_found(**kwargs):
            return {"message": f"Unknown functon call {method_name}", "code": "500"}

        func = getattr(self, method_name, func_not_found)
        return func(**args)

    def read_ledger(self, request):
        return self.main_api.read_ledger(request)

    def pickAnyFile(self):
        file = open_dialog(self.windows["self"])
        if file is None:
            return {"message": "None selected", "code": 0}
        return {"message": f"{file}", "code": 200}

    def pickAnyFolder(self):
        file = open_dialog(self.windows["self"], mode="open_folder")
        if file is None:
            return {"message": "None selected", "code": 0}
        return {"message": f"{file}", "code": 200}

    def getVaultPath(self, window_id):
        folder_path = open_dialog(self.windows[window_id], mode="open_folder")

        self.ledger.set_value("vault_path", folder_path)

        if folder_path is None:
            return {"message": "None selected", "code": 0}
        return {"message": f"{folder_path}", "code": 200}

    def getEntrypointPath(self):
        vault_path = self.ledger.get("vault_path")
        if vault_path == "":
            return {"message": "First set the vault path", "code": 405}

        file_path = open_dialog(self.windows["self"], directory=vault_path, file_types=("Notes (*.md)",))
        self.ledger.set_value("entrypoint_path", file_path)

        if file_path is None:
            return {"message": "None selected", "code": 0}
        else:
            if not Path(file_path).is_relative_to(vault_path):
                self.ledger.set_value("entrypoint_path", "")
                return {"message": "Entrypoint should be located in the vault", "code": 405}

        return {"message": f"{file_path}", "code": 200}

    def getConfigPath(self):
        # get configured value
        config_folder_path = self.ledger.get("config_folder_path")

        if config_folder_path == "":
            # not configured, come up with a good default
            config_folder_path = Path.home().as_posix()
            if Path.home().joinpath(".config").exists():
                config_folder_path = Path.home().joinpath(".config").as_posix()

        # Ask for a new value
        new_config_folder_path = open_dialog(self.windows["self"], mode="open_folder", directory=config_folder_path)

        if new_config_folder_path is None:
            if config_folder_path != "":
                return {"message": config_folder_path, "code": 200}
            else:
                return {"message": "None selected", "code": 200}

        self.ledger.set_value("config_folder_path", new_config_folder_path)

        return {"message": f"{new_config_folder_path}", "code": 200}

    def getRepoPath(self, window_id):
        repo_folder = self.ledger.get("repo_folder_path")

        if repo_folder != "":
            folder = repo_folder
        else:
            folder = Path.home().as_posix()
            if Path.home().joinpath("git").exists():
                folder = Path.home().joinpath("git").as_posix()
            elif Path.home().joinpath("Git").exists():
                folder = Path.home().joinpath("Git").as_posix()

        repo_path = open_dialog(self.windows[window_id], mode="open_folder", directory=folder)

        if repo_path is None:
            self.ledger.set_value("repo_folder_path", "")
            return {"message": "None selected", "code": 0}

        self.ledger.set_value("repo_folder_path", repo_path)
        return {"message": f"{repo_path}", "code": 200}

    def OpenWindowSetupGitpage(self):
        api = self
        html = OpenIncludedFile("installer/setup_gitpages.html")

        self.windows["setup_gitpages"] = webview.create_window("Setup gitpage repo", html=html, js_api=api)

        response = {"message": "new window opened", "code": 200}
        return response

    def openUrlInDefaultBrowser(self, url):
        webbrowser.open(url, new=0, autoraise=True)

    def CheckGithubUsername(self, username):
        r = requests.get(f"https://github.com/{username}")
        if r.status_code == 404:
            return {
                "message": "Username was not found. Tip: the username is not your email address, nor the whole http://github.com/<username> url.",
                "code": 405,
                "data": {},
            }

        # check if repo already exists
        repo_exists = True
        repo_name = f"{username}.github.io"
        self.repo_name = repo_name
        repo_url = f"https://github.com/{username}/{repo_name}"
        self.repo_url = repo_url
        r = requests.get(repo_url)
        if r.status_code == 404:
            repo_exists = False

        return {
            "message": "Success",
            "code": 200,
            "data": {"username": username, "repo_name": repo_name, "repo_url": repo_url, "repo_exists": repo_exists},
        }
        # raise Exception(f'test exception {username}')

    def CheckGit(self):
        issues = []
        good = []
        issue_template = {"name": "", "msg": ""}

        output = os.popen("git --version").read()
        if "git version " in output:
            good.append(f'Git is installed (version: {output.split(" ")[2]})')
        else:
            issue = issue_template.copy()
            issue["name"] = "git_not_installed"
            issue["msg"] = "Git is not installed"
            issues.append(issue)

        output = os.popen("git config --global user.name ").read()
        if output != "":
            good.append(f"Git user.name is configured (value: {output})")
        else:
            issue = issue_template.copy()
            issue["name"] = "git_username_not_configured"
            issue["msg"] = "Git user.name is not configured."
            issues.append(issue)

        output = os.popen("git config --global user.email ").read()
        if output != "":
            good.append(f"Git user.email is configured (value: {output})")
        else:
            issue = issue_template.copy()
            issue["name"] = "git_email_not_configured"
            issue["msg"] = "Git user.email is not configured."
            issues.append(issue)

        message = "<ul>"
        message += " ".join([f'<li><span style="color:green">{x}</span></li>' for x in good])
        if len(issues) > 0:
            message += " ".join([f'<li><span style="color:red">{x["msg"]}</span></li>' for x in issues])

        message += "</ul>"

        response = {"message": message, "code": 200, "data": issues}
        return response

    def SetGitUsername(self, username):
        self.git_username = username
        output = os.popen(f"git config --global user.name {username}").read()
        output = os.popen("git config --global user.name").read()
        if output.strip() == username:
            response = {"message": f"succesfully set username to {output}", "code": 200, "data": ""}
        else:
            print(f'"{output.strip()}"', f'"{username}"')
            response = {"message": f"failed to set username (server returned: {output}", "code": 500, "data": ""}
        return response

    def SetGitEmail(self, email):
        self.git_email = email
        output = os.popen(f"git config --global user.email {email}").read()
        output = os.popen("git config --global user.email").read()
        if output.strip() == email:
            response = {"message": f"succesfully set user.email to {output}", "code": 200, "data": ""}
        else:
            print(f'"{output.strip()}"', f'"{email}"')
            response = {"message": f"failed to set user.email (server returned: {output}", "code": 500, "data": ""}
        return response

    def FlightCheckCloneRepo(self):
        repo_folder_path_str = self.ledger.get("repo_folder_path")
        repo_folder_path = Path(repo_folder_path_str)

        response = {
            "message": f"Will clone repo <b>{self.repo_url}</b> to local path <b>{repo_folder_path_str}</b>.\
                        If that sounds right, click Clone Repo.",
            "code": 200,
            "data": {},
        }

        response["data"]["ready"] = False

        if repo_folder_path.exists():
            if repo_folder_path.joinpath(".git").exists():
                response[
                    "message"
                ] = f"Repo already exists at {repo_folder_path_str}, if this is expected, you can (and should) skip the Clone step.<p>This will <b>overwrite</b> the contents of this repo when you get to publishing!</p>"
                response["data"]["ready"] = True
                self.ledger.set_value("gitpages_configured", True)
            else:
                response["message"] = f"A folder already exists at {repo_folder_path_str}, but it is not a git repo (hidden .git folder is missing)."
                response["message"] += "Delete or move this folder, or pick a different clone path in the previous step before you continue"
                response["code"] = 405

        return response

    def CloneRepo(self):
        response = {"message": "", "code": 200, "data": {"ready": True}}

        repo_folder_path_str = self.ledger.get("repo_folder_path")
        repo_folder_path = Path(repo_folder_path_str)

        # Return ready if git folder already exists according to spec
        if repo_folder_path.joinpath(".git/config").exists():
            with open(repo_folder_path.joinpath(".git/config"), "r", encoding="utf-8") as f:
                content = f.read()
            for l in content.split("\n"):
                if l.strip().startswith("url = "):
                    url = l.strip().replace("url = ", "")

            if url == f"{self.repo_url}.git":
                response["code"] = 200
                response["message"] += " Repo found in the expected location with the expected url. Skipping cloning step, as this is the desired state for this step."
                response["data"] = {"ready": True}
                return response

        # Clone
        process = Popen(["git", "clone", f"{self.repo_url}.git", repo_folder_path_str], stdout=PIPE, stderr=PIPE)

        stdout, stderr = process.communicate()
        stdout = stdout.decode("utf-8")
        stderr = stderr.decode("utf-8")

        # Check result
        response["message"] += f"{stderr}"

        if "fatal:" in stderr:
            response["code"] = 500
            response["data"] = {"ready": False}

        if not repo_folder_path.exists():
            response["code"] = 500
            response["message"] += " Repo not cloned."
            response["data"] = {"ready": False}

        if not repo_folder_path.joinpath(".git").exists():
            response["code"] = 500
            response["message"] += " Local folder found, but .git subfolder is not present."
            response["data"] = {"ready": False}
        else:
            with open(repo_folder_path.joinpath(".git/config"), "r", encoding="utf-8") as f:
                content = f.read()
            for l in content.split("\n"):
                if l.strip().startswith("url = "):
                    url = l.strip().replace("url = ", "")

            if url != f"{self.repo_url}.git":
                response["code"] = 500
                response["message"] += f" Repo url found in .git/config is {url} where {self.repo_url}.git was expected."
                response["data"] = {"ready": False}

        if response["code"] == 200:
            response["message"] += f"<br/>Repo cloned at {repo_folder_path_str}"

        return response

    def presetRepoClonePath(self, repo_name):
        self.config_checker.presetRepoClonePath(repo_name)
        value = self.ledger.get("repo_folder_path")
        return {"message": f"{value}", "code": 200}

    def check_gitpages_configured(self):
        value = self.ledger.get("gitpages_configured")

        if value:
            return {"message": "Gitpage settings are configured", "data": True}
        else:
            return {"message": "Gitpage settings are not yet configured", "data": False}
