from ..lib import OpenIncludedFile, GetIncludedFilePaths
#from .MainApi import Api
from .Api import Api

import threading
import time
import sys
import os
import webview # pywebview

def Launch():
    api = Api()
    api.LaunchWindow(window_id='test', window_title='test api', html_path='test.html', parent_window_id=None)

    webview.start()

def LaunchInstaller():
    # Init
    html = OpenIncludedFile('installer/index.html')
    api = Api()
    api.windows['self'] = webview.create_window('API example', html=html, js_api=api) 

    # Open window
    webview.start()

    # Do stuff
    print(api.msg) 