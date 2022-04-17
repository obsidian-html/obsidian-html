import os                   #
import re                   # regex string finding/replacing
from pathlib import Path    # 
import frontmatter          # remove yaml frontmatter from md files
import urllib.parse         # convert link characters like %
import warnings
import shutil               # used to remove a non-empty directory, copy files
from string import ascii_letters, digits
import tempfile             # used to create temporary files/folders
from shutil import copytree
import time
from functools import cache

# Open source files in the package
import importlib.resources as pkg_resources
import importlib.util
from . import src 

from .PathFinder import get_html_url_prefix
 
class DuplicateFileNameInRoot(Exception):
    pass
class MalformedTags(Exception):
    pass

def printHelpAndExit(exitCode:int):
    print('[Obsidian-html]')
    print('- Add -i </path/to/input.yml> to provide config')
    print('- Add -v for verbose output')
    print('- Add -h to get helptext')
    print('- Add -eht <target/path/file.name> <documentation/tabs/no_tabs> to export the html template.')
    print('- Add -gc to output all configurable keys and their default values.')
    exit(exitCode)

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

def ConvertTitleToMarkdownId(title):
    # remove whitespace and lowercase
    idstr = title.lower().strip()

    # convert "hi hello - 'bye!'" --> "hi-hello---'bye!'" --> "hi-hello-'bye!'"
    idstr = idstr.replace(' ', '-')
    while '--' in idstr:
        idstr = idstr.replace('--', '-')

    # remove special characters "hi-hello-'bye!'" --> "hi-hello-bye"
    idstr = "".join([ch for ch in idstr if ch in (ascii_letters + digits + ' -_')])
    return idstr

@cache
def OpenIncludedFile(resource):
    path = importlib.util.find_spec("obsidianhtml.src").submodule_search_locations[0]
    path = os.path.join(path, resource)
    with open(path, 'r', encoding="utf-8") as f:
        return f.read()

def GetIncludedFilePaths(subpath=''):
    path = importlib.util.find_spec("obsidianhtml.src").submodule_search_locations[0]
    path = os.path.join(path, subpath)
    onlyfiles = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    return onlyfiles

def GetIncludedFilePath(resource):
    path = importlib.util.find_spec("obsidianhtml.src").submodule_search_locations[0]
    return os.path.join(path, resource)

@cache
def OpenIncludedFileBinary(resource):
    path = importlib.util.find_spec("obsidianhtml.src").submodule_search_locations[0]
    path = os.path.join(path, resource)
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

def ExportStaticFiles(pb):
    (obsfolder, static_folder, data_folder, rss_folder) = CreateStaticFilesFolders(pb.paths['html_output_folder'])

    # define files to be copied over (standard copy, static_folder)
    copy_file_list = [
        [f'html/{pb.gc("_css_file")}', 'main.css'], 
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
    if pb.gc('toggles/features/graph/enabled', cached=True):
        copy_file_list.append(['graph/graph.css', 'graph.css'])

    # copy static files over to the static folder
    for file_name in copy_file_list:
        # Get file from package
        c = OpenIncludedFile(file_name[0])

        # Define dest path and html_url_prefix
        dst_path = static_folder.joinpath(file_name[1])
        html_url_prefix = get_html_url_prefix(pb, abs_path_str=dst_path)
        
        # Set pane divs
        toc_pane_div = "right_pane"
        content_pane_div = "left_pane"
        if pb.gc('toggles/features/styling/layout') == 'documentation' and pb.gc('toggles/features/styling/flip_panes'):
            toc_pane_div = "left_pane"
            content_pane_div = "right_pane"

        # Templating
        if file_name[1] in ('main.css', 'obsidian.js'):
            c = c.replace('{html_url_prefix}', html_url_prefix)\
                 .replace('{no_tabs}',str(int(pb.gc('toggles/no_tabs', cached=True))))\
                 .replace('{documentation_mode}',str(int(pb.gc('toggles/features/styling/layout')=='documentation')))\
                 .replace('{toc_pane}',str(int(pb.gc('toggles/features/styling/toc_pane'))))\
                 .replace('{toc_pane_div}', toc_pane_div)\
                 .replace('{content_pane_div}', content_pane_div)
            c = c.replace('__accent_color__', pb.gc('toggles/features/styling/accent_color', cached=True))\
                 .replace('__max_note_width__', pb.gc('toggles/features/styling/max_note_width', cached=True))\

        # Write to dest
        with open (dst_path, 'w', encoding="utf-8") as f:
            f.write(c)

    # copy binary files to dst (byte copy, static_folder)
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
    dst_path = pb.paths['html_output_folder'].joinpath('not_created.html')
    html_url_prefix = get_html_url_prefix(pb, abs_path_str=dst_path)

    with open (dst_path, 'w', encoding="utf-8") as f:
        html = PopulateTemplate(pb, 'none', pb.dynamic_inclusions, pb.html_template, content=c, dynamic_includes='')
        html = html.replace('{html_url_prefix}', html_url_prefix)
        f.write(html)

    c = OpenIncludedFileBinary('html/favicon.ico')
    with open (pb.paths['html_output_folder'].joinpath('favicon.ico'), 'wb') as f:
        f.write(c)

    if pb.gc('toggles/features/graph/enabled', cached=True):
        dst_path = static_folder.joinpath('graph.js')
        html_url_prefix = get_html_url_prefix(pb, abs_path_str=dst_path)

        graph_js= OpenIncludedFile('graph/graph.js')
        graph_js = graph_js.replace('{html_url_prefix}', html_url_prefix)\
                           .replace('{graph_coalesce_force}', pb.gc('toggles/features/graph/coalesce_force', cached=True))\
                           .replace('{no_tabs}',str(int(pb.gc('toggles/no_tabs', cached=True)))) 
        with open (dst_path, 'w', encoding="utf-8") as f:
            f.write(graph_js)

def PopulateTemplate(pb, node_id, dynamic_inclusions, template, content, html_url_prefix=None, title='', dynamic_includes=None, container_wrapper_class_list=None):
    # Cache
    if html_url_prefix is None:
        html_url_prefix = pb.gc("html_url_prefix")

    # Defaults
    if title == '':
        title = pb.gc('site_name', cached=True)
    if dynamic_includes is not None:
        dynamic_inclusions += dynamic_includes

    if pb.config.feature_is_enabled('graph', cached=True):
        dynamic_inclusions += '<link rel="stylesheet" href="'+html_url_prefix+'/obs.html/static/graph.css" />' + "\n"
        dynamic_inclusions += '<script src="https://d3js.org/d3.v4.min.js"></script>' + "\n"

    if pb.config.feature_is_enabled('create_index_from_dir_structure', cached=True):
        dynamic_inclusions += '<script src="'+html_url_prefix+'/obs.html/static/dirtree.js" /></script>' + "\n"

    if container_wrapper_class_list is None:
        container_wrapper_class_list = []
    if pb.gc('toggles/no_tabs', cached=True):
        container_wrapper_class_list.append('single_tab_page')        

    footer_js_inclusions = f'<script src="{html_url_prefix}/obs.html/static/obsidian.js" type="text/javascript"></script>'

    # Include toggled components
    if pb.config.GetCachedConfig('rss_show_icon'):
        code = OpenIncludedFile('rss/button_template.html')
        template = template.replace('{rss_button}', code)
    else:
        template = template.replace('{rss_button}', '')

    if pb.config.GetCachedConfig('dirtree_show_icon'):
        # output path
        output_path = html_url_prefix + '/' + pb.gc('toggles/features/create_index_from_dir_structure/rel_output_path', cached=True)

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
        .replace('{footer_js_inclusions}', footer_js_inclusions)\
        .replace('{html_url_prefix}', html_url_prefix)\
        .replace('{container_wrapper_class_list}', ' '.join(container_wrapper_class_list))\
        .replace('{no_tabs}', str(int(pb.gc('toggles/no_tabs', cached=True))))\
        .replace('{content}', content)

    return template
        # Adding value replacement in content should be done in ConvertMarkdownPageToHtmlPage, 
        # Between the md.StripCodeSections() and md.RestoreCodeSections() statements, otherwise codeblocks can be altered.
        
def CreateTemporaryCopy(source_folder_path, pb):
    # Create temp dir
    tmpdir = tempfile.TemporaryDirectory()

    print(f"> COPYING VAULT {source_folder_path} TO {tmpdir.name}")

    if pb.gc('toggles/verbose_printout'):
        print('\tWill overwrite paths: obsidian_folder, obsidian_entrypoint')    
    
    # Copy vault to temp dir
    copytree(source_folder_path, tmpdir.name, dirs_exist_ok=True)
    print("< COPYING VAULT: Done")

    return tmpdir