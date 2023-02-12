import webview  # pywebview


def open_dialog(window, mode="open_file", file_types=None, directory="", allow_multiple=False):
    """Returns tuple (when allow_multiple==True), string (when allow_multiple==False), or None (when canceled)"""

    if file_types is None:
        file_types = ("All files (*.*)",)

    print(mode, directory)
    if mode == "open_file":
        result = window.create_file_dialog(webview.OPEN_DIALOG, directory=directory, allow_multiple=allow_multiple, file_types=file_types)
    elif mode == "open_folder":
        result = window.create_file_dialog(webview.FOLDER_DIALOG, directory=directory, allow_multiple=allow_multiple)
    else:
        raise Exception(f"mode {mode} unknown")

    if result is None:
        return None
    if allow_multiple:
        return result
    return result[0]
