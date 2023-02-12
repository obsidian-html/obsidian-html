from ..lib import OpenIncludedFile

# from .MainApi import Api
from .Api import Api

import webview  # pywebview


def Launch():
    api = Api()
    api.LaunchWindow(window_id="test", window_title="test api", html_path="test.html", parent_window_id=None)

    webview.start()


def LaunchInstaller():
    # Init
    html = OpenIncludedFile("installer/index.html")
    api = Api()
    api.wm.windows["self"] = webview.create_window("API example", html=html, js_api=api)

    # Open window
    webview.start()
