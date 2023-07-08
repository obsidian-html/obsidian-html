import json
import yaml
from pathlib import Path

from ..lib import get_arguments_dict, OpenIncludedFile, get_obshtml_appdir_folder_path, formatted_print


def Config():
    args = get_arguments_dict()
    if len(args["command"]) == 1 or args["command"][1] not in ["list", "info", "set", "delete", "rename"]:
        print_help_and_exit(0)
    subcommand = args["command"][1]

    globals()[f"config_{subcommand}"](args)


# --- handle configs file creation / fetching
def get_configs_file_default_contents():
    return json.dumps({}, indent=2)


def get_configs_file_path():
    return get_obshtml_appdir_folder_path().joinpath("configs.json")


def ensure_configs_file():
    """Ensures that the configs file exists, including its parent dirs"""
    configs_file_path = get_configs_file_path()
    if not configs_file_path.exists():
        configs_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(configs_file_path, "w") as f:
            f.write(get_configs_file_default_contents())
    ensure_configs_file_valid_contents()

    return configs_file_path


def ensure_configs_file_valid_contents():
    """Ensures that the configs file contains valid json, if not, replace the contents with default empty structure"""
    try:
        with open(get_configs_file_path(), "r") as f:
            return json.loads(f.read())
    except:
        with open(get_configs_file_path(), "w") as f:
            f.write(get_configs_file_default_contents())


def get_configs():
    configs_file_path = ensure_configs_file()
    with open(configs_file_path, "r") as f:
        return json.loads(f.read())


def store_configs(configs):
    configs_file_path = ensure_configs_file()
    with open(configs_file_path, "w") as f:
        f.write(json.dumps(configs, indent=2))


# --- subcommands
def config_info(args):
    configs_file_path = ensure_configs_file()
    existence = "(non-existent)"
    if configs_file_path.exists():
        existence = ""
    print(f"Configurations file: {configs_file_path.as_posix()} {existence}")


def config_set(args):
    # get current configs
    configs = get_configs()

    # check input
    arg_failure = False
    if "alias" not in args:
        formatted_print("ERROR", '"400: --alias" is required for subcommand `set`.')
        arg_failure = True
    if "file" not in args:
        formatted_print("ERROR", '"400: --file" is required for subcommand `set`.')
        arg_failure = True
    if arg_failure:
        formatted_print("ERROR", "400: Required arguments not passed in. Run `obsidianhtml config` to get help text.")
        exit(1)

    alias = args["alias"]
    if alias == "" or alias is None:
        formatted_print("ERROR", '"400: --alias" requires a value.')
        arg_failure = True
    file_path = Path(args["file"]).resolve()

    if file_path.exists() == False:
        formatted_print("ERROR", f"Config file {file_path} does not exist")
        exit(1)

    # feedback
    verb = "Added"
    if alias in configs.keys():
        verb = "Altered"
    formatted_print("INFO", f"{verb} config {alias}")

    # update configs
    configs[alias] = {"file": file_path.as_posix()}
    store_configs(configs)


def config_list(args):
    configs = get_configs()
    default_config = yaml.safe_load(OpenIncludedFile("defaults_config.yml"))

    def get_entrypoint(config):
        skip_md = False
        if "toggles" in config and "compile_md" in config["toggles"] and config["toggles"]["compile_md"] == False:
            skip_md = True
        if skip_md == False:
            if "obsidian_entrypoint_path_str" in config:
                return config["obsidian_entrypoint_path_str"]
        else:
            if "md_entrypoint_path_str" in config:
                return config["md_entrypoint_path_str"]
            elif "md_folder_path_str" in config:
                return Path(config["md_folder_path_str"]).joinpath("index.md").as_posix()

    def get_markdown_output_folder(config, default_config):
        skip_md = False
        if "toggles" in config and "compile_md" in config["toggles"] and config["toggles"]["compile_md"] == False:
            skip_md = True
        if skip_md == True:
            return ""

        if "md_folder_path_str" in config:
            return config["md_folder_path_str"]
        else:
            return "./" + default_config["md_folder_path_str"]

    def get_html_output_folder(config, default_config):
        skip_html = False
        if "toggles" in config and "compile_html" in config["toggles"] and config["toggles"]["compile_html"] == False:
            skip_html = True
        if skip_html == True:
            return ""

        if "html_output_folder_path_str" in config:
            return config["html_output_folder_path_str"]
        else:
            return "./" + default_config["html_output_folder_path_str"]

    for alias in configs:
        with open(configs[alias]["file"], "r") as f:
            config = yaml.safe_load(f.read())

        configs[alias]["entrypoint"] = get_entrypoint(config)

        md_output_folder = get_markdown_output_folder(config, default_config)
        if md_output_folder != "":
            configs[alias]["md_output_folder"] = md_output_folder

        html_output_folder = get_html_output_folder(config, default_config)
        if html_output_folder != "":
            configs[alias]["html_output_folder"] = html_output_folder

    print(json.dumps(configs, indent=2))


def config_rename(args):
    configs = get_configs()

    # check input
    arg_failure = False
    if "old" not in args:
        formatted_print("ERROR", '"400: --old" is required for subcommand `rename`.')
        arg_failure = True
    if "new" not in args:
        formatted_print("ERROR", '"400: --new" is required for subcommand `rename`.')
        arg_failure = True
    if arg_failure:
        formatted_print("ERROR", "400: Required arguments not passed in. Run `obsidianhtml config` to get help text.")
        exit(1)

    old = args["old"]
    new = args["new"]
    if old not in configs.keys():
        formatted_print("ERROR", f'400: Alias "{old}" does not exist')
        exit(1)

    configs[new] = configs[old].copy()
    del configs[old]
    store_configs(configs)

    formatted_print("INFO", f"Renamed config {old} to {new}")


def config_delete(args):
    configs = get_configs()

    # check input
    arg_failure = False
    if "alias" not in args:
        formatted_print("ERROR", '"400: --alias" is required for subcommand `delete`.')
        arg_failure = True
    if arg_failure:
        formatted_print("ERROR", "400: Required arguments not passed in. Run `obsidianhtml config` to get help text.")
        exit(1)

    alias = args["alias"]
    if alias not in configs.keys():
        formatted_print("ERROR", f'400: Alias "{alias}" does not exist')
        exit(1)

    del configs[alias]
    store_configs(configs)

    formatted_print("INFO", f"Deleted config {alias}")


# --- supporting functions
def print_help_and_exit(exitCode: int):
    print(OpenIncludedFile("help_texts/config_help_text"))
    exit(exitCode)


# --- provided functions
def get_config_by_alias(alias):
    configs = get_configs()
    if alias not in configs.keys():
        formatted_print("ERROR", f'Alias "{alias}" not known. Known aliases: {list(configs.keys())}')
        return None
    return configs[alias]
