from ..lib import OpenIncludedFile

import webview  # pywebview


class WindowManager:
    api = None
    windows = None

    def __init__(self, api):
        self.windows = {}
        self.api = api

    def LaunchWindow(self, window_id, window_title, html_path, parent_window_id=None):
        # test if window exists
        if window_id in self.windows.keys():
            raise Exception(f"Window with window_id {window_id} already exists. Call ActivateWindow() instead.")

        self.CreateWindow(window_id, window_title, html_path, parent_window_id)

    def ActivateWindow(self, window_id):
        # test if window exists
        if window_id not in self.windows.keys():
            raise Exception(f"Window with window_id {window_id} does not exist. Call LaunchWindow() instead.")

        # [todo] figure out how to raise the window on top

    def DestroyWindow(self, window_id):
        # test if window exists
        if window_id not in self.windows.keys():
            raise Exception(f"Window with window_id {window_id} does not exist. Cannot destroy.")

        # destroy window object
        self.windows[window_id]["window"].destroy()

        # activate parent window (necessary?)
        self.ActivateWindow(self.windows[window_id]["parent_id"])

        # remove window record from the window manager
        self.windows.pop("window_id", None)

    def CreateWindow(self, window_id, window_title, html_path, parent_window_id=None):
        # fetch html
        html = OpenIncludedFile("installer/dist/" + html_path)

        # template html
        html = html.replace("{{window_id}}", window_id)

        # create record for window
        self.windows[window_id] = {"parent_id": parent_window_id, "window_title": window_title, "html_path": html_path, "window": None}

        # create window
        self.windows[window_id]["window"] = webview.create_window(window_title, html=html, js_api=self.api)
