import os
import sys
import http.server
import socketserver
from pathlib import Path

# Defer tools
from contextlib import ExitStack
from functools import partial


def ServeDir(port=8888, directory="./"):
    # Get directory/port from commandline args if provided
    if len(sys.argv) > 2:
        if sys.argv[1] == "serve":
            for i, v in enumerate(sys.argv):
                if v == "--directory":
                    if len(sys.argv) < (i + 2):
                        print("No directory path given for serve.\n  Use `obsidianhtml serve --directory /target/path/to/html/folder` to provide input.")
                        exit(1)
                    directory = sys.argv[i + 1]

                if v == "--port":
                    if len(sys.argv) < (i + 2):
                        print("No port given for serve.\n  Use `obsidianhtml serve --port 8654` to provide input.")
                        exit(1)
                    port = sys.argv[i + 1]

    if not Path(directory).resolve().exists():
        print(f"Configured directory of {directory} does not exist.")
        exit(1)

    # We do this trickery so that we can set Handler.directory without having the init method overwrite our setting.
    # (Handler.init() is called somewhere out of our control)
    class BetterHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            if self.directory is None:
                self.directory = os.getcwd()

            self.directory = os.fspath(self.directory)
            super(http.server.SimpleHTTPRequestHandler, self).__init__(*args, **kwargs)

    # configure server
    Handler = BetterHandler
    Handler.directory = Path(directory).resolve().as_posix()
    Handler.extensions_map.update(
        {
            ".js": "application/javascript",
        }
    )

    # start server
    print(
        f"OBSHTML: Started webserver at http://localhost:{port}/ hosting from {Path(directory).resolve().as_posix()} (Ctrl+C to exit)",
        flush=True,
    )
    httpd = socketserver.TCPServer(("", int(port)), Handler)

    with ExitStack() as stack:
        stack.callback(partial(httpd.server_close))
        stack.callback(partial(print, "DEFERRED: closed webserver", flush=True))

        httpd.serve_forever()
