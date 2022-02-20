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
 
class DuplicateFileNameInRoot(Exception):
    pass
class MalformedTags(Exception):
    pass

def printHelpAndExit(exitCode:int):
    print('[Obsidian-html]')
    print('- Add -i </path/to/input.yml> to provide config')
    print('- Add -v for verbose output')
    print('- Add -h to get helptext')
    print('- Add -eht <target/path/file.name> to export the html template.')
    print('- Add -gc to output all configurable keys and their default values.')
    exit(exitCode)

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
    idstr = "".join([ch for ch in idstr if ch in (ascii_letters + digits + ' -_')])
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

def ExportStaticFiles(pb, graph_enabled, html_url_prefix, site_name):
    obsfolder = pb.paths['html_output_folder'].joinpath('obs.html')
    os.makedirs(obsfolder, exist_ok=True)
    static_folder = obsfolder.joinpath('static')
    os.makedirs(static_folder, exist_ok=True)
    data_folder = obsfolder.joinpath('data')
    os.makedirs(data_folder, exist_ok=True)
    rss_folder = obsfolder.joinpath('rss')
    os.makedirs(rss_folder, exist_ok=True)

    # copy files over (standard copy, static_folder)
    copy_file_list = [
        ['html/main.css','main.css'], 
        ['html/obsidian.js', 'obsidian.js'],
        ['html/mermaid.css', 'mermaid.css'],
        ['html/mermaid.min.js', 'mermaid.min.js'],
        ['html/taglist.css', 'taglist.css'],
        ['html/external.svg', 'external.svg'],
        ['html/hashtag.svg', 'hashtag.svg'],
        ['rss/rss.svg', 'rss.svg'],
        ['index_from_dir_structure/dirtree.js', 'dirtree.js'],
        ['index_from_dir_structure/dirtree.svg', 'dirtree.svg'],
    ]
    if graph_enabled:
        copy_file_list.append(['graph/graph.css', 'graph.css'])

    for file_name in copy_file_list:
        c = OpenIncludedFile(file_name[0])
        
        if file_name[1] in ('main.css'):
            c = c.replace('{html_url_prefix}', html_url_prefix)

        with open (static_folder.joinpath(file_name[1]), 'w', encoding="utf-8") as f:
            f.write(c)

    # copy files over (byte copy, static_folder)
    copy_file_list_byte = [
        ['html/SourceCodePro-Regular.ttf', 'SourceCodePro-Regular.ttf'],
        ['html/Roboto-Regular.ttf', 'Roboto-Regular.ttf']
    ]
    for file_name in copy_file_list_byte:
        c = OpenIncludedFileBinary(file_name[0])
        with open (static_folder.joinpath(file_name[1]), 'wb') as f:
            f.write(c)

    # Custom copy
    c = OpenIncludedFile('html/not_created.html')
    with open (pb.paths['html_output_folder'].joinpath('not_created.html'), 'w', encoding="utf-8") as f:
        html = PopulateTemplate(pb, 'none', site_name, html_url_prefix, pb.dynamic_inclusions, pb.html_template, content=c, dynamic_includes='')
        html = html.replace('{html_url_prefix}', html_url_prefix)
        f.write(html)

    c = OpenIncludedFileBinary('html/favicon.ico')
    with open (pb.paths['html_output_folder'].joinpath('favicon.ico'), 'wb') as f:
        f.write(c)

    if pb.gc('toggles','features','graph','enabled'):
        graph_js= OpenIncludedFile('graph/graph.js')
        graph_js = graph_js.replace('{html_url_prefix}', pb.gc('html_url_prefix'))\
                           .replace('{graph_coalesce_force}', pb.gc('toggles','features','graph','coalesce_force'))
        with open (static_folder.joinpath('graph.js'), 'w', encoding="utf-8") as f:
            f.write(graph_js)

def PopulateTemplate(pb, node_id, site_name, html_url_prefix, dynamic_inclusions, template, content, title='', dynamic_includes=None):
    # Defaults
    if title == '':
        title = site_name
    if dynamic_includes is not None:
        dynamic_inclusions += dynamic_includes

    # Include toggled components
    if pb.gc('toggles','features','rss','enabled') and pb.gc('toggles','features','rss','styling','show_icon'):
        code = OpenIncludedFile('rss/button_template.html')
        template = template.replace('{rss_button}', code)
    else:
        template = template.replace('{rss_button}', '')

    if pb.gc('toggles','features','create_index_from_dir_structure','enabled') and pb.gc('toggles','features','create_index_from_dir_structure','styling','show_icon'):
        # output path
        output_path = pb.gc('html_url_prefix') + '/' + pb.gc('toggles','features','create_index_from_dir_structure','rel_output_path')

        # compile template
        code = OpenIncludedFile('index_from_dir_structure/button_template.html')
        code = code.replace('{dirtree_index_path}', output_path)

        # add to main template
        template = template.replace('{dirtree_button}', code)
    else:
        template = template.replace('{dirtree_button}', '')

    # Replace placeholders
    template = template\
        .replace('{node_id}', node_id)\
        .replace('{title}', title)\
        .replace('{dynamic_includes}', dynamic_inclusions)\
        .replace('{html_url_prefix}', html_url_prefix)\
        .replace('{content}', content)

    return template
        # Adding value replacement in content should be done in ConvertMarkdownPageToHtmlPage, 
        # Between the md.StripCodeSections() and md.RestoreCodeSections() statements, otherwise codeblocks can be altered.
        
def CreateTemporaryCopy(source_folder_path, pb):
    # Create temp dir
    tmpdir = tempfile.TemporaryDirectory()

    print(f"> COPYING VAULT {source_folder_path} TO {tmpdir.name}")

    if pb.gc('toggles','verbose_printout'):
        print('\tWill overwrite paths: obsidian_folder, obsidian_entrypoint')    
    
    # Copy vault to temp dir
    copy_tree(source_folder_path, tmpdir.name, preserve_times=1)
    print("< COPYING VAULT: Done")

    return tmpdir
    

def MergeDictRecurse(base_dict, update_dict, path=''):
    helptext = '\n\nTip: Run obsidianhtml -gc to see all configurable keys and their default values.\n'

    for k, v in update_dict.items():
        key_path = '/'.join(x for x in (path, k) if x !='')

        # every configured key should be known in base config, otherwise this might suggest a typo/other error
        if k not in base_dict.keys():
            raise Exception(f'\n\tThe configured key "{key_path}" is unknown. Check for typos/indentation. {helptext}')

        # don't overwrite a dict in the base config with a string, or something else
        # in general, we don't expect types to change
        if type(base_dict[k]) != type(v):
            raise Exception(f'\n\tThe value of key "{key_path}" is expected to be of type {type(base_dict[k])}, but is of type {type(v)}. {helptext}')

        # dict match -> recurse
        if isinstance(base_dict[k], dict) and isinstance(v, dict):
            base_dict[k] = MergeDictRecurse(base_dict[k], update_dict[k], path=key_path)
            continue
        
        # other cases -> copy over
        if isinstance(update_dict[k], list):
            base_dict[k] = v.copy()
        else:
            base_dict[k] = v

    return base_dict.copy()

def CheckConfigRecurse(config, path='', match_str='<REQUIRED_INPUT>'):
    helptext = '\n\nTip: Run obsidianhtml -gc to see all configurable keys and their default values.\n'

    for k, v in config.items():
        key_path = '/'.join(x for x in (path, k) if x !='')
        
        if isinstance(v, dict):
            CheckConfigRecurse(config[k], path=key_path)

        if v == match_str:
            raise Exception(f'\n\tKey "{key_path}" is required. {helptext}')