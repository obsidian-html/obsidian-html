from ..lib import OpenIncludedFile
from .MainApi import Api

import threading
import time
import sys
import os
import webview # pywebview

def LaunchInstaller():
    # Init
    html = OpenIncludedFile('installer/index.html')
    api = Api()
    api.window = webview.create_window('API example', html=html, js_api=api)

    # Open window
    webview.start()

    # Do stuff
    print(api.msg) 