import os                   #
import re                   # regex string finding/replacing
import yaml
import frontmatter          # remove yaml frontmatter from md files
import warnings
import shutil               # used to remove a non-empty directory, copy files
import tempfile             # used to create temporary files/folders
import time
import unicodedata
import glob

import urllib.parse         # convert link characters like %

from pathlib import Path    # 
from string import ascii_letters, digits
from functools import cache
from subprocess import Popen, PIPE
from appdirs import AppDirs

# Open source files in the package
import importlib.resources as pkg_resources
import importlib.util

from . import src 
 
class DuplicateFileNameInRoot(Exception):
    pass
class MalformedTags(Exception):
    pass

def print_global_help_and_exit(exitCode:int):
    print()
    version = OpenIncludedFile('version')
    print(OpenIncludedFile('help_texts/help_text').replace('{version}', version))
    exit(exitCode)

def get_obshtml_appdir_folder_path():
    return Path(AppDirs("obsidianhtml", "obsidianhtml").user_config_dir)

def get_default_appdir_config_yaml_path():
    appdir_config_folder_path = get_obshtml_appdir_folder_path()
    return appdir_config_folder_path.joinpath('config.yml')

def WriteFileLog(files, log_file_name, include_processed=False):
    if include_processed:
        s = "| key | processed note? | processed md? | note | markdown | html | html link relative | html link absolute |\n|:---|:---|:---|:---|:---|:---|:---|:---|\n"
    else:
        s = "| key | note | markdown | html | html link relative | html link absolute |\n|:---|:---|:---|:---|:---|:---|\n"

    for k in files.keys():
        fo = files[k]
        n = ''
        m = ''
        h = ''
        if 'note' in fo.path.keys():
            n = fo.path['note']['file_absolute_path']
        if 'markdown' in fo.path.keys():
            m = fo.path['markdown']['file_absolute_path']
        if 'html' in fo.path.keys():
            # temp
            fo.get_link('html')
            h = fo.path['html']['file_absolute_path']
        if 'html' in fo.link.keys():
            hla = fo.link['html']['absolute']
            hlr = fo.link['html']['relative']

        if include_processed:
            s += f"| {k} | {fo.processed_ntm} | {fo.processed_mth} | {n} | {m} | {h} | {hlr} | {hla} |\n"
        else:
            s += f"| {k} | {n} | {m} | {h} | {hlr} | {hla} |\n"

    with open(log_file_name, 'w', encoding='utf-8') as f:
        f.write(s)

def simpleHash(text:str):
    hash=0
    for ch in text:
        hash = ( hash*281  ^ ord(ch)*997) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
    return str(hash)


def ConvertTitleToMarkdownId(title):
    # remove whitespace and lowercase
    idstr = title.lower().strip()

    # remove special characters "hi-hello-'bye!'" --> "hi-hello-bye"
    idstr = "".join([ch for ch in idstr if ch in (ascii_letters + digits + ' -_')])

    # convert "hi hello - 'bye!'" --> "hi-hello---'bye!'" --> "hi-hello-'bye!'"
    idstr = idstr.replace(' ', '-')
    while '--' in idstr:
        idstr = idstr.replace('--', '-')

    return idstr

def slugify(value, separator='-', unicode=False, skip_chars_re=''):
    """ Slugify a string, to make it URL friendly. """
    if not unicode:
        # Replace Extended Latin characters with ASCII, i.e. žlutý → zluty
        value = unicodedata.normalize('NFKD', value)
        value = value.encode('ascii', 'ignore').decode('ascii')
    
    value = re.sub(r'[^\w\s\-' + skip_chars_re + ']', ' ', value).strip().lower()
    return re.sub(r'[{}\s]+'.format(separator), separator, value)


@cache
def GetIncludedResourcePath(resource):
    path = importlib.util.find_spec("obsidianhtml.src").submodule_search_locations[0]
    return Path(os.path.join(path, resource))

@cache
def OpenIncludedFile(resource):
    path = GetIncludedResourcePath(resource)
    with open(path, 'r', encoding="utf-8") as f:
        return f.read()

def GetIncludedFilePaths(subpath=''):
    path = importlib.util.find_spec("obsidianhtml.src").submodule_search_locations[0]
    path = os.path.join(path, subpath)
    onlyfiles = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    return onlyfiles

@cache
def OpenIncludedFileBinary(resource):
    path = GetIncludedResourcePath(resource)
    with open(path, 'rb') as f:
        return f.read()    

@cache
def CreateStaticFilesFolders(html_output_folder):
    obsfolder = html_output_folder.joinpath('obs.html')
    os.makedirs(obsfolder, exist_ok=True)

    static_folder = obsfolder.joinpath('static')
    os.makedirs(static_folder, exist_ok=True)

    data_folder = obsfolder.joinpath('data')
    os.makedirs(data_folder, exist_ok=True)

    rss_folder = obsfolder.joinpath('rss')
    os.makedirs(rss_folder, exist_ok=True)

    return (obsfolder, static_folder, data_folder, rss_folder)



def is_installed(command):
    try:
        p = Popen([command], stdout=PIPE, stderr=PIPE)
        output, error = p.communicate()
    except FileNotFoundError as ex:
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
        command = command.split(' ')
    p = Popen(command, stdout=PIPE, stderr=PIPE)
    output, error = p.communicate()

    return output.decode('ascii').replace('\\n', '\n').strip()

def FindVaultByEntrypoint(entrypoint_path):
    vault_found = False

    # Allow both folders and entrypoint notes to be passed in
    search_folder = Path(entrypoint_path)
    if not search_folder.is_dir():
        search_folder = search_folder.parent

    history = search_folder.as_posix()
    while not vault_found: 
        try:
            history += '\n' + search_folder.as_posix()
            if search_folder.as_posix() == '/':
                print(history)
                return False
            for folder in [ f for f in os.scandir(search_folder) if f.is_dir(follow_symlinks=False) ]:
                if (folder.name == '.obsidian'):
                    return search_folder.resolve().as_posix()
            search_folder = search_folder.parent
        except Exception as ex:
            print(ex)
            return False
    return False

def get_rel_html_url_prefix(rel_path):
    depth = rel_path.count('/')
    if depth > 0:
        prefix = ('../'*depth)[:-1]
    else:
        prefix = '.'
    return prefix

def get_html_url_prefix(pb, rel_path_str=None, abs_path_str=None):
    # check input and convert rel_path_str from abs_path_str if necessary
    if rel_path_str is None:
        if abs_path_str is None:
            raise Exception("pass in either rel_path_str or abs_path_str")
        rel_path_str = Path(abs_path_str).relative_to(pb.paths['html_output_folder']).as_posix()

    # return html_prefix
    if pb.gc('toggles/relative_path_html', cached=True):
        html_url_prefix = pb.sc(path='html_url_prefix', value=get_rel_html_url_prefix(rel_path_str))
    else:
        html_url_prefix = pb.gc('html_url_prefix')
    return html_url_prefix