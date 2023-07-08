import sys
import yaml
from pathlib import Path
import tempfile

from ..lib import print_global_help_and_exit
from ..lib import (
    find_vault_folder_by_entrypoint,
    OpenIncludedFile,
    YamlIndentDumper,
    get_obshtml_appdir_folder_path,
    get_default_appdir_config_yaml_path,
)

from .ConvertVault import ConvertVault

# Defer tools
from contextlib import ExitStack
from functools import partial
import subprocess
import time


def Run():
    # to be configured by commandline args
    config_path_str = ""
    entrypoint_path_str = ""
    output_folder_path_str = ""
    clean_toggle = False
    subfolder = ""

    # internal vars
    output_folder_path = None
    host_dir_path = None
    appdir_config_folder_path = get_obshtml_appdir_folder_path()
    config_save_path = get_default_appdir_config_yaml_path()

    for i, v in enumerate(sys.argv):
        if v == "-i":
            if len(sys.argv) < (i + 2):
                print("No config path given.\n  Use `obsidianhtml run -i /target/path/to/config.yml` to provide input.")
                print_global_help_and_exit(1)
            config_path_str = sys.argv[i + 1]
        elif v == "-f":
            if len(sys.argv) < (i + 2):
                print("No entrypoint path given.\n  Use `obsidianhtml run -f /target/path/to/entrypoint.md` to provide input.")
                print_global_help_and_exit(1)
            entrypoint_path_str = sys.argv[i + 1]
        elif v == "-o":
            if len(sys.argv) < (i + 2):
                print("No output folder path given.\n  Use `obsidianhtml run -o /target/path/to/output/folder` to provide input.")
                print_global_help_and_exit(1)
            output_folder_path_str = sys.argv[i + 1]

        elif v == "--clean":
            clean_toggle = True
        elif v == "--subfolder":
            if len(sys.argv) < (i + 2):
                print("No subfolder path given.\n  Use `obsidianhtml run --subfolder test to provide input.")
                print_global_help_and_exit(1)
            subfolder = sys.argv[i + 1]

    # Load config
    config = yaml.safe_load(OpenIncludedFile("defaults_config.yml"))
    del config["html_output_folder_path_str"]
    del config["md_folder_path_str"]
    del config["md_entrypoint_path_str"]
    del config["toggles"]["no_tabs"]

    if config_path_str:
        with open(config_path_str, "r") as f:
            provided_config = yaml.safe_load(f)
        config.update(provided_config)

    # Set entrypoint path
    def TestEntryPointExists(entrypoint_path_str):
        entrypoint_path = Path(entrypoint_path_str).resolve()
        entrypoint_abs_path_posix = entrypoint_path.as_posix()
        if not entrypoint_path.exists():
            print(f"Could not find provided config file at {entrypoint_abs_path_posix}, is the path correct?")
            print_global_help_and_exit(1)
        return entrypoint_path, entrypoint_abs_path_posix

    entrypoint_path = None
    if entrypoint_path_str:
        entrypoint_path, entrypoint_abs_path_posix = TestEntryPointExists(entrypoint_path_str)
        config["obsidian_entrypoint_path_str"] = entrypoint_abs_path_posix
        print_set_var(config, "obsidian_entrypoint_path_str", reason="provided by user through commandline", category="info")
    else:
        if config["obsidian_entrypoint_path_str"] == "<REQUIRED_INPUT>":
            print("ERROR: Entrypoint path not provided, supply either a path directly via -f or via a config file (-i)")
            print_global_help_and_exit(1)
        else:
            entrypoint_path, entrypoint_abs_path_posix = TestEntryPointExists(config["obsidian_entrypoint_path_str"])
            config["obsidian_entrypoint_path_str"] = entrypoint_abs_path_posix
            print_set_var(config, "obsidian_entrypoint_path_str", reason="provided by user through config file", category="info")

    # find vault folder based on entrypoint
    result = find_vault_folder_by_entrypoint(config["obsidian_entrypoint_path_str"])
    if result:
        config["obsidian_folder_path_str"] = result
        print_set_var(config, "obsidian_folder_path_str", reason="deduced", category="info")
    else:
        print(
            f"ERROR: Obsidian vault not found based on entrypoint {config['obsidian_folder_path_str']}.\n\tDid you provide a note that is in a valid vault? (Tip: `obsidianhtml run` looks for the .obsidian folder)"
        )
        print_global_help_and_exit(1)

    # Set/overwrite html_url_prefix
    if subfolder != "":
        if subfolder[0] != "/":
            subfolder = "/" + subfolder
        if subfolder[-1] == "/":
            subfolder = subfolder[:-1]
        config["html_url_prefix"] = subfolder
        print_set_var(config, "html_url_prefix", reason="provided by user through commandline", category="info")

    # If user sets md_entrypoint_path_str but not md_folder_path_str, the former should be overwritten as md_folder_path_str.parent
    # This is confusing, so don't allow this
    if "md_entrypoint_path_str" in config.keys() and "md_folder_path_str" not in config.keys():
        config["md_folder_path_str"] = Path(config["md_entrypoint_path_str"]).resolve().parent.as_posix()
        print_set_var(config, "md_folder_path_str", reason="based on other provided user setting from the config file", category="info")
        print(
            "WARNING: md_folder_path_str was automatically filled in because it was absent, but md_entrypoint_path_str was present.\n\tThis might not be what you want. Either remove md_entrypoint_path_str from your config, or add md_folder_path_str to your config explicitly to remove this warning."
        )
    if "md_folder_path_str" in config.keys() and "md_entrypoint_path_str" not in config.keys():
        config["md_entrypoint_path_str"] = Path(config["md_folder_path_str"]).resolve().joinpath("index.md").as_posix()
        print_set_var(config, "md_entrypoint_path_str", reason="based on other provided user setting from the config file", category="info")
        print(
            "WARNING: md_entrypoint_path_str was automatically filled in because it was absent, but md_folder_path_str was present.\n\tThis might not be what you want. Either remove md_folder_path_str from your config, or add md_entrypoint_path_str to your config explicitly to remove this warning."
        )

    # set output folder
    output_folder_path_as_posix = ""
    if "md_folder_path_str" not in config or "html_output_folder_path_str" not in config:
        if output_folder_path_str:
            output_folder_path = Path(output_folder_path_str).resolve()
            output_folder_path_as_posix = output_folder_path.as_posix()
            print(f"INFO: Internal config var was set. (provided by user through commandline):\n\t[internal] output_folder_path: {output_folder_path_as_posix} ")
        else:
            print("INFO: Creating tempdir")
            with tempfile.TemporaryDirectory(prefix="obshtml_") as tempdir_path:
                output_folder_path = Path(tempdir_path).resolve()
                output_folder_path_as_posix = output_folder_path.as_posix()
                print("INFO: Created temporary directory", output_folder_path_as_posix)
                print(f"INFO: Internal config var was set. (provided by user through commandline):\n\t[internal] output_folder_path: {output_folder_path_as_posix} ")

    # set md_folder_path
    md_folder_path = None
    if "md_folder_path_str" not in config:
        md_folder_path = output_folder_path.joinpath("md").resolve()
    else:
        md_folder_path = Path(config["md_folder_path_str"]).resolve()
    CleanFolder(md_folder_path, clean_toggle)
    config["md_folder_path_str"] = md_folder_path.as_posix()
    print_set_var(config, "md_folder_path_str", reason="default behavior", category="info")

    # set md_entrypoint_path_str
    if "md_entrypoint_path_str" not in config:
        config["md_entrypoint_path_str"] = md_folder_path.joinpath("index.md").as_posix()
        print_set_var(config, "md_entrypoint_path_str", reason="default behavior", category="info")
    else:
        print_set_var(config, "md_entrypoint_path_str", reason="provided by user through config file", category="info")

    # set html_output_folder_path
    html_output_folder_path = None
    if "html_output_folder_path_str" not in config:
        html_output_folder_path = output_folder_path.joinpath("html").resolve()
    else:
        html_output_folder_path = Path(config["html_output_folder_path_str"]).resolve()
    host_dir_path = html_output_folder_path

    html_url_prefix = config["html_url_prefix"]
    if html_url_prefix != "":
        if not isinstance(html_url_prefix, str):
            print(f"ERROR: type if html_url_prefix is {type(html_url_prefix).__name__} where string was expected.")
            exit(1)
        if html_output_folder_path.name != html_url_prefix:
            html_output_folder_path = html_output_folder_path.joinpath(config["html_url_prefix"][1:]).resolve()

    CleanFolder(html_output_folder_path, clean_toggle)
    config["html_output_folder_path_str"] = html_output_folder_path.as_posix()
    print_set_var(config, "html_output_folder_path_str", reason="default behavior", category="info")

    # write config to file
    appdir_config_folder_path.mkdir(parents=True, exist_ok=True)
    with open(config_save_path, "w", encoding="utf-8") as f:
        f.write(yaml.dump(config, Dumper=YamlIndentDumper, sort_keys=False))

    # convert vault using new config yaml
    ConvertVault(config_save_path.as_posix())

    print(f"\nGenerated config yaml saved to {config_save_path}")
    print("\nTip: use this command next to _only_ convert your vault using these saved settings, and not start a webserver:")
    print(f"\n\tobsidianhtml convert -i {config_save_path}\n")

    # Start webserver
    # ----------------------------
    # defer context for webserver
    with ExitStack() as stack:
        cmd = []
        if sys.argv[0].split("/")[-1] == "obsidianhtml":
            cmd = ["obsidianhtml", "serve"]
        else:
            cmd = ["python", "-m", "obsidianhtml", "serve"]

        cmd += ["--directory", host_dir_path.as_posix(), "--port", "8888"]

        webserver_process = subprocess.Popen(cmd)

        # close server *always* on exit
        stack.callback(partial(webserver_process.terminate))
        stack.callback(partial(print, "DEFERRED: closed webserver", flush=True))

        time.sleep(0.5)
        try:  # we have an endless process so we will get a timeout error
            outs, errs = webserver_process.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            pass
        if webserver_process.returncode is None:  # no return code means that the process is still running, any serious error will have caused the process to quit.
            print(f"\nOpen your webbrowser and navigate to http://localhost:8888{html_url_prefix}/ to view your website")
            input("Press enter to stop hosting website and exit obsidianhtml run.\n\n")


def CleanFolder(folder_path, clean_toggle):
    folder_path_as_posix = folder_path.as_posix()
    if folder_path.exists():
        if clean_toggle:
            print(f"INFO: Output folder path ({folder_path_as_posix}) already exists, removing (due to --clean being set)")
            print(f"shutil.rmtree('{folder_path_as_posix}')")
        else:
            print(f"ERROR: Set output folder path ({folder_path_as_posix}) already exists, canceling run.\n\tUse --clean to allow obsidianhtml to remove this directory for you")
            print_global_help_and_exit(1)
    else:
        # folder_path.mkdir(parents=True, exist_ok=True)
        print(f"INFO: Created empty output folder path {folder_path}")


def TestConfig(config):
    problems = []
    # If user sets md_entrypoint_path_str but not md_folder_path_str, the former would be overwritten
    # This is confusing, so don't allow this
    if "md_entrypoint_path_str" in config.keys() and "md_folder_path_str" not in config.keys():
        problems.append("md_entrypoint_path_str")


def print_set_var(config, key, reason="", category="info", skip_header=False):
    prefix = ""
    if category == "info":
        prefix = "INFO:"
    elif category == "error":
        prefix = "ERROR:"

    if reason:
        reason = f"({reason})"

    key_msg = f"{key}: {config[key]}"
    if not skip_header:
        print(f"{prefix} Config var was set. {reason}")

    print(f"\t{key_msg}")
