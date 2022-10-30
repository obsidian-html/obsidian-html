import sys
import yaml
from pathlib import Path

from .lib import print_global_help_and_exit
from .lib import    OpenIncludedFile, GetIncludedResourcePath, fetch_str

from .ConvertVault import ConvertVault
from .Run import Run
from .Export import RunExport
from .Serve import ServeDir
from .EmbeddedSearch import CliEmbeddedSearch




def main():
    # Show help text
    # ---------------------------------------------------------
    if '-h' in sys.argv or '--help' in sys.argv or 'help' in sys.argv:
        print_global_help_and_exit(0)

    # Commands
    # ---------------------------------------------------------
    if len(sys.argv) < 2 or sys.argv[1][0] == '-':
        print('DEPRECATION WARNING: You did not pass in a command. Assuming you meant "convert". Starting version 4.0.0 providing a command will become mandatory.')
        command = 'convert'
    else:
        command = sys.argv[1]

    if command == 'convert':
        ConvertVault()
    elif command == 'run':
        Run()
    elif command == 'export':
        RunExport()
    elif command == 'version':
        short_hash = None
        try:
            git_folder_path = GetIncludedResourcePath('').parent.parent.joinpath('.git')
            if git_folder_path.exists():
                short_hash = fetch_str('git rev-parse --short HEAD')
        except:
            pass
        version = OpenIncludedFile('version')
        if short_hash is not None:
            print(version, f"commit:{short_hash}")
        else:
            print(version)
        exit()
    elif command == 'serve':
        ServeDir()
        exit()
    elif command == 'search':
        CliEmbeddedSearch()
        exit()

    else:
        print(f'Command "{command}" is unknown')
        print_global_help_and_exit(1)

