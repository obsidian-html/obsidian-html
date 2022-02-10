import os                   #
import re                   # regex string finding/replacing
from pathlib import Path    # 
import frontmatter          # remove yaml frontmatter from md files
import urllib.parse         # convert link characters like %
import warnings
import shutil               # used to remove a non-empty directory, copy files
from string import ascii_letters, digits
import tempfile             # used to create temporary files/folders
from distutils.dir_util import copy_tree
import time

# Open source files in the package
import importlib.resources as pkg_resources
import importlib.util
from . import src 
 
# Lookup tables
image_suffixes = ['jpg', 'jpeg', 'gif', 'png', 'bmp', 'pdf']

class DuplicateFileNameInRoot(Exception):
    pass
class MalformedTags(Exception):
    pass

def GetObsidianFilePath(link, file_tree):
    # Remove possible alias suffix, folder prefix, and add '.md' to get a valid lookup key
    # a link can look like this: folder/note#chapter|alias
    # then filename=note, header=chapter
    parts = link.split('|')[0].split('/')[-1].split('#')
    filename = parts[0]
    header = ''
    if len(parts) > 1:
        header = parts[1]

    if filename[-3:] != '.md':
        filename += '.md'
        
    # Return tuple
    if filename not in file_tree.keys():
        return (filename, False, '')

    return (filename, file_tree[filename], header)

def IsValidLocalMarkdownLink(full_file_path_str):
    page_path = Path(full_file_path_str).resolve()

    if page_path.exists() == False:
        return False
    if page_path.suffix != '.md':
        return False

    return True

def ConvertTitleToMarkdownId(title):
    idstr = title.lower().strip()
    idstr = idstr.replace(' ', '-')
    while '--' in idstr:
        idstr = idstr.replace('--', '-')
    idstr = "".join([ch for ch in idstr if ch in (ascii_letters + digits + ' -')])
    return idstr

def OpenIncludedFile(resource):
    path = importlib.util.find_spec("obsidianhtml.src").submodule_search_locations[0]
    path = os.path.join(path, resource)
    with open(path, 'r', encoding="utf-8") as f:
        return f.read()

def OpenIncludedFileBinary(resource):
    path = importlib.util.find_spec("obsidianhtml.src").submodule_search_locations[0]
    path = os.path.join(path, resource)
    with open(path, 'rb') as f:
        return f.read()    

def ExportStaticFiles(pb):
    static_folder = pb.paths['html_output_folder'].joinpath('98682199-5ac9-448c-afc8-23ab7359a91b-static')
    os.makedirs(static_folder, exist_ok=True)

    # copy files over (standard copy, static_folder)
    copy_file_list = ['main.css', 'mermaid.css', 'mermaid.min.js', 'taglist.css', 'external.svg']
    if pb.config['toggles']['features']['graph']['enabled']:
        copy_file_list += ['graph.css']

    for file_name in copy_file_list:
        c = OpenIncludedFile(file_name)
        
        if file_name in ('main.css'):
            c = c.replace('{html_url_prefix}', pb.config['html_url_prefix'])

        with open (static_folder.joinpath(file_name), 'w', encoding="utf-8") as f:
            f.write(c)

    # copy files over (byte copy, static_folder)
    copy_file_list_byte = ['SourceCodePro-Regular.ttf']
    for file_name in copy_file_list_byte:
        c = OpenIncludedFileBinary(file_name)
        with open (static_folder.joinpath(file_name), 'wb') as f:
            f.write(c)

    # Custom copy
    c = OpenIncludedFile('not_created.html')
    with open (pb.paths['html_output_folder'].joinpath('not_created.html'), 'w', encoding="utf-8") as f:
        html = PopulateTemplate(pb, pb.html_template, content=c, dynamic_includes='')
        html = html.replace('{html_url_prefix}', pb.config['html_url_prefix'])
        f.write(html)

    c = OpenIncludedFileBinary('favicon.ico')
    with open (pb.paths['html_output_folder'].joinpath('favicon.ico'), 'wb') as f:
        f.write(c)

def PopulateTemplate(pb, template, content, title='', dynamic_includes=None):
    # Defaults
    if title == '':
        title = pb.config['site_name']
    if dynamic_includes is None:
        dynamic_includes = pb.dynamic_inclusions

    return template\
        .replace('{title}', title)\
        .replace('{dynamic_includes}', pb.dynamic_inclusions)\
        .replace('{html_url_prefix}', pb.config['html_url_prefix'])\
        .replace('{content}', content)

        # Adding value replacement in content should be done in ConvertMarkdownPageToHtmlPage, 
        # Between the md.StripCodeSections() and md.RestoreCodeSections() statements, otherwise codeblocks can be altered.
        
def CreateTemporaryCopy(source_folder_path):
    # Create temp dir
    tmpdir = tempfile.TemporaryDirectory()
    
    # Copy vault to temp dir
    print(f"> COPYING VAULT {source_folder_path} TO {tmpdir.name}", end=' ')
    copy_tree(source_folder_path, tmpdir.name, preserve_times=1)
    print("< DONE")

    return tmpdir
    