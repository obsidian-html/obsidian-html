import sys

from .lib import print_global_help_and_exit, get_arguments_dict, formatted_print
from .lib import OpenIncludedFile, GetIncludedResourcePath, fetch_str

from .controller.ConvertVault import ConvertVault
from .controller.Run import Run
from .controller.Export import RunExport
from .controller.Serve import ServeDir
from .controller.Config import Config
from .features.EmbeddedSearch import CliEmbeddedSearch


def main():
    # Show help text
    # ---------------------------------------------------------
    if "-h" in sys.argv or "--help" in sys.argv or "help" in sys.argv:
        print_global_help_and_exit(0)

    # Commands
    # ---------------------------------------------------------
    # Set default command
    args = get_arguments_dict()

    command = args["command"]
    main_command = command[0]

    # Execute command
    if main_command == "convert":
        ConvertVault()
    elif main_command == "config":
        Config()
    elif main_command == "export":
        RunExport()
    elif main_command == "version":
        short_hash = None
        try:
            git_folder_path = GetIncludedResourcePath("").parent.parent.joinpath(".git")
            if git_folder_path.exists():
                short_hash = fetch_str("git rev-parse --short HEAD")
        except:
            pass
        version = OpenIncludedFile("version")
        if short_hash is not None:
            print(version, f"commit:{short_hash}")
        else:
            print(version)
        exit()
    elif main_command == "serve":
        ServeDir()
        exit()
    elif main_command == "search":
        CliEmbeddedSearch()
        exit()
    elif main_command == "help":
        print_global_help_and_exit(0)
    elif main_command == "short_help":
        print_global_help_and_exit(1, "help_texts/short_help_text")
    else:
        formatted_print("ERROR", f'Command "{main_command}" is unknown')
        print_global_help_and_exit(1, "help_texts/short_help_text")
