import sys
from pathlib import Path

from ..lib import OpenIncludedFile


def RunExport():
    # Export packaged html template so users can edit it and then use their custom template
    # ---------------------------------------------------------
    command = ""

    # determine command
    if len(sys.argv) < 3:
        print_export_help_and_exit(1)
    else:
        command = sys.argv[2]

    # get global args
    for i, v in enumerate(sys.argv):
        if v == "-h" or v == "--help":
            print_export_help_and_exit(0)

    # run command
    if command == "layout":
        return ExportLayout()
    elif command == "default-config":
        return ExportDefaultConfig()
    else:
        print(f"Command {command} is unknown")
        print_export_help_and_exit(1)


def ExportLayout():
    # get args
    for i, v in enumerate(sys.argv):
        if v == "-o":
            if len(sys.argv) < (i + 2):
                print("No output path given.\n  Use `obsidianhtml export -o /target/path/to/template.html` to provide input.")
                print_export_help_and_exit(1)
            else:
                export_html_template_target_path = Path(sys.argv[i + 1]).resolve()

        if v == "-l":
            if len(sys.argv) < (i + 2):
                print("No layout name given.\n  Use `obsidianhtml export -l <documentation/tabs/no_tabs>` to provide input.")
                print_export_help_and_exit(1)
            else:
                layout = sys.argv[i + 1]

    # check args
    if layout not in ["documentation", "tabs", "no_tabs", "minimal"]:
        print(f"Provided layout name of {layout} is unknown.\n  Use `obsidianhtml export layout -l <documentation/tabs/no_tabs/minimal>` to provide input.")
        print_export_help_and_exit(1)

    # Create parent folders
    export_html_template_target_path.parent.mkdir(parents=True, exist_ok=True)
    html = OpenIncludedFile(f"html/layouts/template_{layout}.html")

    # Export file
    with open(export_html_template_target_path, "w", encoding="utf-8") as t:
        t.write(html)

    print(f"Exported html template to {str(export_html_template_target_path)}")
    exit(0)


def ExportDefaultConfig():
    output_path = None

    # get args
    for i, v in enumerate(sys.argv):
        if v == "-o":
            if len(sys.argv) < (i + 2):
                print("No output path given.\n  Use `obsidianhtml export default-config -o /save/location.yml` to provide input.")
                print_export_help_and_exit(1)
            else:
                output_path = Path(sys.argv[i + 1]).resolve()

    # get config
    yml = OpenIncludedFile("defaults_config.yml")

    # Print or write
    if output_path is not None:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(yml)
        print(f"Exported default config yaml to {str(output_path)}")
    else:
        print(yml)


def print_export_help_and_exit(exitCode: int):
    print(OpenIncludedFile("help_texts/export_help_text"))
    exit(exitCode)
