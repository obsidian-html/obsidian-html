import os
import sys
import http.server
import socketserver
from pathlib import Path

def ServeDir(port=8888, directory='./'):
    # Get directory/port from commandline args if provided
    if len(sys.argv) > 2:
        if sys.argv[1] == 'serve':
            for i, v in enumerate(sys.argv):
                if v == '--directory':
                    if len(sys.argv) < (i + 2):
                        print(f'No directory path given for serve.\n  Use `obsidianhtml serve --directory /target/path/to/html/folder` to provide input.')
                        exit(1)
                    directory = sys.argv[i+1]

                if v == '--port':
                    if len(sys.argv) < (i + 2):
                        print(f'No port given for serve.\n  Use `obsidianhtml serve --port 8654` to provide input.')
                        exit(1)
                    port = sys.argv[i+1]

    if not Path(directory).resolve().exists():
        print(f'Configured directory of {directory} does not exist.')
        exit(1)

    # move to dir to serve from there
    os.chdir(directory)

    # configure server
    Handler = http.server.SimpleHTTPRequestHandler
    Handler.extensions_map.update({
        ".js": "application/javascript",
    })

    # start server
    httpd = socketserver.TCPServer(("", int(port)), Handler)
    httpd.serve_forever()