from ..lib import OpenIncludedFile
from .InstallerApi import InstallerApi

import threading
import time
import sys
import os
import webview # pywebview

class Api:
    msg = None
    window = None
    installer_window = None
    testval = 0

    # Helper objects
    ledger = None
    config_checker = None


    def __init__(self):
        self.ledger = Ledger()
        self.config_checker = ConfigChecker(self)

    def LaunchVaultGithubPagesInstaller(self):
        api = InstallerApi(self)
        html = OpenIncludedFile('installer/gp_installer.html')

        api.windows['self'] = webview.create_window('GithubPages Installer', html=html, js_api=api)
        self.installer_window = api.window

        response = {
            'message': 'installer running'
        }
        return response

    def test(self):
        self.testval += 1
        response = {
            'message': f'{self.testval}'
        }
        return response

    def getVersion(self):
        stream = os.popen('pip show obsidianhtml')
        output = stream.read()
        response = {
            'message': output
        }
        return response

    def error(self):
        raise Exception('This is a Python exception')

    def temp_SetupGitpages(self):
        api = InstallerApi(self.window)
        api.OpenWindowSetupGitpage()

        response = {
            'message': 'installer running'
        }
        return response        

class Ledger:
    ledger = None

    def __init__(self):
        self.ledger = {}
        self.ledger['vault_path'] = ''
        self.ledger['entrypoint_path'] = ''
        self.ledger['config_folder_path'] = ''

    def get(self, value_id):
        # Get value
        if value_id not in self.ledger.keys():
            raise Exception(f'key {value_id} not present in ledger')

        value = self.ledger[value_id]

        # Set default
        return value

    def set_value(self, id, value):
        if id == 'vault_path':
            return self.set_vault_path(value)
        elif id == 'entrypoint_path':
            return self.set_entrypoint_path(value)
        elif id == 'config_folder_path':
            return self.set_config_folder_path(value)            
        else:
            raise Exception(f'id {id} not known (Ledger.set_value())')

    def set_vault_path(self, value):
        self.ledger['vault_path'] = value
    def set_entrypoint_path(self, value):
        self.ledger['entrypoint_path'] = value
    def set_config_folder_path(self, value):
        self.ledger['config_folder_path'] = value        


class ConfigChecker:
    main_api = None
    ledger = None
    def __init__(self, main_api):
        self.main_api = main_api
        self.ledger = main_api.ledger
