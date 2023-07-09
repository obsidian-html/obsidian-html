import os
import sys
import re  # regex string finding/replacing
import yaml
import json
import unicodedata

from pathlib import Path  #
from string import ascii_letters, digits
from functools import cache
from subprocess import Popen, PIPE
from appdirs import AppDirs

# Open source files in the package
import importlib.util

# from . import src


class DuplicateFileNameInRoot(Exception):
    pass


class MalformedTags(Exception):
    pass


def print_global_help_and_exit(exitCode: int, help_file="help_texts/help_text"):
    print()
    version = OpenIncludedFile("version")
    print(OpenIncludedFile(help_file).replace("{version}", version))
    exit(exitCode)


def get_obshtml_appdir_folder_path():
    return Path(AppDirs("obsidianhtml", "obsidianhtml").user_config_dir)


def get_default_appdir_config_yaml_path():
    appdir_config_folder_path = get_obshtml_appdir_folder_path()
    return appdir_config_folder_path.joinpath("config.yml")


def WriteFileLog(files, log_file_name, include_processed=False):
    if include_processed:
        s = "| key | processed note? | processed md? | note | markdown | html | html link relative | html link absolute |\n|:---|:---|:---|:---|:---|:---|:---|:---|\n"
    else:
        s = "| key | note | markdown | html | html link relative | html link absolute |\n|:---|:---|:---|:---|:---|:---|\n"

    for k in files.keys():
        fo = files[k]
        n = ""
        m = ""
        h = ""
        if "note" in fo.path.keys():
            n = fo.path["note"]["file_absolute_path"]
        if "markdown" in fo.path.keys():
            m = fo.path["markdown"]["file_absolute_path"]
        if "html" in fo.path.keys():
            # temp
            fo.get_link("html")
            h = fo.path["html"]["file_absolute_path"]
        if "html" in fo.link.keys():
            hla = fo.link["html"]["absolute"]
            hlr = fo.link["html"]["relative"]

        if include_processed:
            s += f"| {k} | {fo.processed_ntm} | {fo.processed_mth} | {n} | {m} | {h} | {hlr} | {hla} |\n"
        else:
            s += f"| {k} | {n} | {m} | {h} | {hlr} | {hla} |\n"

    with open(log_file_name, "w", encoding="utf-8") as f:
        f.write(s)


def simpleHash(text: str):
    hash = 0
    for ch in text:
        hash = (hash * 281 ^ ord(ch) * 997) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
    return str(hash)


def ConvertTitleToMarkdownId(title):
    # remove whitespace and lowercase
    idstr = title.lower().strip()

    # remove special characters "hi-hello-'bye!'" --> "hi-hello-bye"
    idstr = "".join([ch for ch in idstr if ch in (ascii_letters + digits + " -_")])

    # convert "hi hello - 'bye!'" --> "hi-hello---'bye!'" --> "hi-hello-'bye!'"
    idstr = idstr.replace(" ", "-")
    while "--" in idstr:
        idstr = idstr.replace("--", "-")

    return idstr


def slugify_path(value, separator="-", unicode=False, skip_chars_re=r"/\."):
    # avoids "test?.html" turning into "test-.html" instead of "test.html"
    suffix = ""
    if value.endswith(".html"):
        value = re.sub(r'\.html$', '', value)
        suffix = ".html"
    
    slugified_value = slugify(value, separator, unicode, skip_chars_re)
    return f'{slugified_value}{suffix}'


def slugify(value, separator="-", unicode=False, skip_chars_re=""):
    """Slugify a string, to make it URL friendly."""
    if not unicode:
        # Replace Extended Latin characters with ASCII, i.e. žlutý → zluty
        value = unicodedata.normalize("NFKD", value)
        value = value.encode("ascii", "ignore").decode("ascii")

    value = re.sub(r"[^\w\s\-" + skip_chars_re + "]", " ", value).strip().lower()
    return re.sub(r"[{}\s]+".format(separator), separator, value)


@cache
def GetIncludedResourcePath(resource):
    path = importlib.util.find_spec("obsidianhtml.src").submodule_search_locations[0]
    return Path(os.path.join(path, resource))


@cache
def OpenIncludedFile(resource):
    path = GetIncludedResourcePath(resource)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def GetIncludedFilePaths(subpath=""):
    path = importlib.util.find_spec("obsidianhtml.src").submodule_search_locations[0]
    path = os.path.join(path, subpath)
    onlyfiles = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    return onlyfiles


@cache
def OpenIncludedFileBinary(resource):
    path = GetIncludedResourcePath(resource)
    with open(path, "rb") as f:
        return f.read()


@cache
def CreateStaticFilesFolders(html_output_folder):
    obsfolder = html_output_folder.joinpath("obs.html")
    os.makedirs(obsfolder, exist_ok=True)

    static_folder = obsfolder.joinpath("static")
    os.makedirs(static_folder, exist_ok=True)

    data_folder = obsfolder.joinpath("data")
    os.makedirs(data_folder, exist_ok=True)

    rss_folder = obsfolder.joinpath("rss")
    os.makedirs(rss_folder, exist_ok=True)

    return (obsfolder, static_folder, data_folder, rss_folder)


def is_installed(command):
    try:
        p = Popen([command], stdout=PIPE, stderr=PIPE)
        output, error = p.communicate()
    except FileNotFoundError:
        return False
    return True


def should_ignore(ignore, path):
    if ignore is None:
        return False

    for ignore_path in [Path(x).resolve() for x in ignore]:
        if ignore_path.as_posix() == path.as_posix():
            return True
        if ignore_path.is_dir() and path.is_relative_to(ignore_path):
            return True

    return False


class YamlIndentDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(YamlIndentDumper, self).increase_indent(flow, False)


def pushd(path):
    cwd = os.getcwd()
    os.chdir(path)
    return cwd


def fetch_str(command):
    if isinstance(command, str):
        command = command.split(" ")
    p = Popen(command, stdout=PIPE, stderr=PIPE)
    output, error = p.communicate()

    return output.decode("ascii").replace("\\n", "\n").strip()


def find_vault_folder_by_entrypoint(entrypoint_path):
    """Starts at the entrypoint and returns the first parent that contains a '.obsidian' folder"""
    vault_found = False

    # Allow both folders and entrypoint notes to be passed in
    search_folder = Path(entrypoint_path)
    if not search_folder.is_dir():
        search_folder = search_folder.parent

    history = search_folder.as_posix()
    while not vault_found:
        try:
            history += "\n" + search_folder.as_posix()
            if search_folder.as_posix() == "/":
                print(history)
                return False
            for folder in [f for f in os.scandir(search_folder) if f.is_dir(follow_symlinks=False)]:
                if folder.name == ".obsidian":
                    return search_folder.resolve().as_posix()
            search_folder = search_folder.parent
        except Exception as ex:
            print(ex)
            return False
    return False


def get_rel_html_url_prefix(rel_path):
    depth = rel_path.count("/")
    if depth > 0:
        prefix = ("../" * depth)[:-1]
    else:
        prefix = "."
    return prefix


def get_html_url_prefix(pb, rel_path_str=None, abs_path_str=None):
    # check input and convert rel_path_str from abs_path_str if necessary
    if rel_path_str is None:
        if abs_path_str is None:
            raise Exception("pass in either rel_path_str or abs_path_str")
        rel_path_str = Path(abs_path_str).relative_to(pb.paths["html_output_folder"]).as_posix()

    # return html_prefix
    if pb.gc("toggles/relative_path_html", cached=True):
        html_url_prefix = pb.sc(path="html_url_prefix", value=get_rel_html_url_prefix(rel_path_str))
    else:
        html_url_prefix = pb.gc("html_url_prefix")
    return html_url_prefix


def retain_reference(*args):
    """Goal of this function is to trick people and linters into thinking that the reference is "used".
    This is necessary for e.g. tempdir references, where if we don't catch the returned value in
    a reference, the tempdir is immediately removed.
    """
    for arg in args:
        pass


def expect_list(var):
    """Will wrap any non-list type in a list, will return an empty list if 'var is None'"""
    if var is None:
        return list()
    return list(var)


def MergeDictRecurse(base_dict, update_dict, path=""):
    helptext = "\n\nTip: Run \`obsidianhtml export default-config\` to see all configurable keys and their default values.\n"

    # these dicts are freeform, and thus should not be checked
    excluded_key_paths = ["module_config"]

    def check_leaf(key_path, val, new_val):
        if val == "<REMOVED>":
            raise Exception(
                f"\n\tThe setting {key_path} has been removed. Please remove it from your settings file. See https://obsidian-html.github.io/Configurations/Deprecated%20Configurations/Deprecated%20Configurations.html for more information."
            )
        elif val == "<DEPRECATED>":
            print(
                f"DEPRECATION WARNING: The setting {key_path} is deprecated. See https://obsidian-html.github.io/Configurations/Deprecated%20Configurations/Deprecated%20Configurations.html for more information."
            )
            return False
        elif key_path == "toggles/strict_line_breaks":
            if isinstance(new_val, bool) or new_val == "auto":
                return False
            raise Exception(f'Error: the value of toggles/strict_line_breaks should be one of: True, False, "auto". Got: {new_val}')
        return True

    for k, v in update_dict.items():
        key_path = "/".join(x for x in (path, k) if x != "")

        # every configured key should be known in base config, otherwise this might suggest a typo/other error
        if k not in base_dict.keys():
            raise Exception(f'\n\tThe configured key "{key_path}" is unknown. Check for typos/indentation. {helptext}')

        # don't overwrite a dict in the base config with a string, or something else
        # in general, we don't expect types to change
        if type(base_dict[k]) != type(v):
            if check_leaf(key_path, base_dict[k], v):
                raise Exception(f'\n\tThe value of key "{key_path}" is expected to be of type {type(base_dict[k])}, but is of type {type(v)}. {helptext}')

        # dict match -> recurse
        if isinstance(base_dict[k], dict) and isinstance(v, dict):
            if key_path in excluded_key_paths:
                base_dict[k] = update_dict[k].copy()
            else:
                base_dict[k] = MergeDictRecurse(base_dict[k], update_dict[k], path=key_path)
            continue

        # other cases -> copy over
        if isinstance(update_dict[k], list):
            base_dict[k] = v.copy()
        else:
            check_leaf(key_path, base_dict[k], v)
            base_dict[k] = v

    return base_dict.copy()


def formatted_print(level, msg):
    lines = msg.split("\n")
    print(f"[{level.upper():^7}] * {lines[0]}")
    if len(lines) == 1:
        return
    for line in lines[1:]:
        print(f"{'':^9}   {line}")


# --- parse commandline
def get_arguments_dict():
    def determine_command():
        if len(sys.argv) < 2:
            formatted_print("ERROR", "400: You did not pass in a command. If you want to convert your vault, run `obsidianhtml convert [arguments]`")
            return ["short_help"]

        if "-h" in sys.argv or "--help" in sys.argv or "help" in sys.argv:
            return ["help"]

        command = []
        for i, v in enumerate(sys.argv[1:]):
            if v[0] == "-":
                break
            command.append(v)

        if len(command) == 0:
            formatted_print("ERROR", "400: You did not pass in a command. If you want to convert your vault, run `obsidianhtml convert [arguments]`")
            return ["short_help"]

        return command

    def determine_config_path():
        for i, v in enumerate(sys.argv):
            if v == "-i":
                if len(sys.argv) < (i + 2):
                    formatted_print("error", "No config path given.\n  Use `obsidianhtml convert -i /target/path/to/config.yml` to provide input.")
                    exit(1)
                return sys.argv[i + 1]
        return ""

    def determine_verbose_overwrite():
        for i, v in enumerate(sys.argv):
            if v == "-v":
                return True
        return False

    def collect_literals():
        literals = {}
        valued_args = ["-i", "-f"]
        non_valued_args = ["-v"]
        for i, v in enumerate(sys.argv):
            if v in valued_args:
                literals[v] = None
                if len(sys.argv) >= (i + 2):
                    literals[v] = sys.argv[i + 1]
                continue
            if v in non_valued_args:
                literals[v] = None
                continue
        return literals

    def collect_dynamic_arguments(arguments):
        for i, v in enumerate(sys.argv):
            if v.startswith("--"):
                key = v[2:]
                if key in arguments.keys():
                    raise Exception(f'400: Trying to set existing {key} in arguments dict (value provided through "{v}"). This is not allowed.')
                if len(sys.argv) >= (i + 2):
                    value = sys.argv[i + 1]
                    if value.startswith("--"):
                        formatted_print("ERROR", f'400: Trying to set variable "{key}" to value "{value}".\nVariable values cannot start with "--".')
                        exit(1)
                    arguments[key] = sys.argv[i + 1]

    arguments = {}
    arguments["command"] = determine_command()
    arguments["config_path"] = determine_config_path()
    arguments["literals"] = collect_literals()
    collect_dynamic_arguments(arguments)

    if determine_verbose_overwrite():
        arguments["verbose"] = True
    return arguments


def bisect(input, separator, squash_tail=False):
    """Will split a string into exactly two parts: (rest, value)
    - If split returns a list with a single element, no value was found (value = ""), input string is returned as rest.
    - If the split creates more than 2 values, an error will occur, unless squash_tail is set to True
      - Add a comment to the function call why squash_tail is necessary, as this setting can cause headaches!
    """

    if input == "":
        return "", ""

    parts = input.split(separator)

    if len(parts) == 1:
        rest = parts[0]
        value = ""
        return rest, value
    if len(parts) == 2:
        rest = parts[0]
        value = parts[1]
        return rest, value

    if squash_tail:
        rest = parts.pop(0)
        value = separator.join(parts)
        return rest, value

    raise Exception(f'500: Bisect resulted in {len(parts)} parts where 1 or 2 were expected. Input: "{input}", separator: "{separator}", parts: {parts}')


def strip_frontmatter(content):
    """
        [enter yaml]
          if first non-empty line = "---" (no whitespace allowed) -> enter yaml
          else -> return none
        [exit yaml]
          if line = "---" (no whitespace allowed) -> exit yaml        
        [in yaml]
          write line to text with newline
    """

    first_line = True
    in_yaml = False
    text = []
    
    lines = content.split("\n")
    for line in lines:
        if first_line:
            # don't test on newlines
            if len(line) == 0:
                continue

            # first line not a newline, begin in earnest
            first_line = False

            # first line is exactly "---" -> we have a yaml block
            if line == "---":
                in_yaml = True
                continue

            # first line is not exactly "---" -> we don't have a yaml block
            return content

        
        # exit yaml block
        if line == "---":
            in_yaml = False
            continue
        
        # don't record yaml lines
        if in_yaml:
            continue

        text.append(line)

    return "\n".join(text)