from ..lib import OpenIncludedFile

from .WindowManager import WindowManager
from .Ledger import Ledger
from .ConfigChecker import ConfigChecker
from .lib import open_dialog

from pathlib import Path

import threading
import time
import sys
import os
import webview # pywebview



class Api:
    def __init__(self):
        self.wm = WindowManager(self)
        self.ledger = Ledger()
        self.config_checker = ConfigChecker(self)

    def get_window(self, args):
        return self.wm.windows[args['window_id']]['window']

    def call(self, args):
        a = args['action'] 
        if a == 'action/get_vault_path':
            return self.get_vault_path(args)
        elif a ==  'action/get_entrypoint_path':
            return self.get_entrypoint_path(args)
        else:
            print(f'Action path {a} unknown.')
            raise Exception(f'Action path {a} unknown.')

    def get_vault_path(self, args):
        folder_path = open_dialog(self.get_window(args), mode="open_folder")

        self.ledger.set_value('vault_path', folder_path)

        if folder_path is None:
            args['message'] = 'None selected'
            args['code'] = 0
            return args
        
        args['message'] = f'{folder_path}'
        args['code'] = 200
        return args

    def get_entrypoint_path(self, args):
        vault_path = self.ledger.get('vault_path')
        if vault_path == '':
            args['message'] = 'First set the vault path'
            args['code'] = 405
            return args
        
        file_path = open_dialog(self.get_window(args), directory=vault_path, file_types=('Notes (*.md)',))
        self.ledger.set_value('entrypoint_path', file_path)

        if file_path is None:
            args['message'] = 'None selected'
            args['code'] = 0
            return args
        else:
            if not Path(file_path).is_relative_to(vault_path):
                self.ledger.set_value('entrypoint_path', '')
                args['message'] = 'Entrypoint should be located in the vault'
                args['code'] = 405                
                return args

        args['message'] = f'{file_path}'
        args['code'] = 200
        return args

    def LaunchWindow(self, window_id, window_title, html_path, parent_window_id = None):
        # html_path: relative to obsidianhtml/src/installer/dist/
        self.wm.LaunchWindow(window_id, window_title, html_path, parent_window_id)
