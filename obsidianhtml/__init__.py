from __future__ import annotations
from array import array
import sys                  # commandline arguments
import os                   #
import shutil               # used to remove a non-empty directory, copy files
import uuid
import regex as re          # regex string finding/replacing
from pathlib import Path    # 
import markdown             # convert markdown to html
import yaml
import urllib.parse         # convert link characters like %
import frontmatter
import json
import warnings
import time
import datetime
import platform

from .PathFinder import OH_File, get_rel_html_url_prefix, get_html_url_prefix

from .MarkdownPage import MarkdownPage
from .MarkdownLink import MarkdownLink
from .lib import    DuplicateFileNameInRoot, CreateTemporaryCopy, \
                    GetObsidianFilePath, OpenIncludedFile, ExportStaticFiles, \
                    PopulateTemplate, \
                    printHelpAndExit, WriteFileLog
from .PicknickBasket import PicknickBasket

from .CreateIndexFromTags import CreateIndexFromTags
from .CreateIndexFromDirStructure import CreateIndexFromDirStructure
from .RssFeed import RssFeed

# Open source files in the package
import importlib.resources as pkg_resources
import importlib.util
from . import src


def recurseObisidianToMarkdown(fo:'OH_File', pb, log_level=1):
    '''This functions converts an obsidian note to a markdown file and calls itself on any local note links it finds in the page.'''

    # Unpack so we don't have to type too much.
    paths = pb.paths        # Paths of interest, such as the output and input folders
    files = pb.files        # Hashtable of all files found in the obsidian vault

    # Don't parse if not parsable
    if not fo.metadata['is_parsable_note']:
        return

    # Convert note to markdown
    # ------------------------------------------------------------------
    # Create an object that handles a lot of the logic of parsing the page paths, content, etc
    md = MarkdownPage(pb, fo, 'note', files)

    # The bulk of the conversion process happens here
    md.ConvertObsidianPageToMarkdownPage()

    # The frontmatter was stripped from the obsidian note prior to conversion
    # Add yaml frontmatter back in
    md.page = (frontmatter.dumps(frontmatter.Post("", **md.metadata))) + '\n' + md.page

    # Save file
    # ------------------------------------------------------------------
    # Create folder if necessary
    dst_path = fo.path['markdown']['file_absolute_path']
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    # Write markdown to file
    with open(dst_path, 'w', encoding="utf-8") as f:
        f.write(md.page)

    # Recurse for every link in the current page
    # ------------------------------------------------------------------
    for l in md.links:
        link = GetObsidianFilePath(l, files)
        link_name = link[0]
        lo = link[1]

        if lo == False or lo.processed_ntm == True:
            if pb.gc('toggles/verbose_printout', cached=True):
                if lo == False:
                    print('\t'*log_level, f"Skipping converting {l}, link not internal or not valid.")
                else:
                    print('\t'*log_level, f"Skipping converting {l}, already processed.")
            continue

        # Mark the file as processed so that it will not be processed again at a later stage
        lo.processed_ntm = True

        # Convert the note that is linked to
        if pb.gc('toggles/verbose_printout', cached=True):
            print('\t'*log_level, f"found link {lo.path['note']['file_absolute_path']} (through parent {fo.path['note']['file_absolute_path']})")

        recurseObisidianToMarkdown(lo, pb, log_level=log_level)

def ConvertMarkdownPageToHtmlPage(fo:'OH_File', pb, backlinkNode=None, log_level=1):
    '''This functions converts a markdown page to an html file and calls itself on any local markdown links it finds in the page.'''
    
    # Unpack picknick basket so we don't have to type too much.
    paths = pb.paths                    # Paths of interest, such as the output and input folders
    files = pb.files                    # Hashtable of all files found in the obsidian vault

    # Don't parse if not parsable
    if not fo.metadata['is_parsable_note']:
        return

    page_path = fo.path['markdown']['file_absolute_path']
    rel_dst_path = fo.path['html']['file_relative_path']

    if pb.gc('toggles/relative_path_html', cached=True):
        html_url_prefix = pb.sc(path='html_url_prefix', value=get_rel_html_url_prefix(rel_dst_path.as_posix()))
    else:
        html_url_prefix = pb.gc('html_url_prefix')

    # Load contents
    # ------------------------------------------------------------------
    # Create an object that handles a lot of the logic of parsing the page paths, content, etc
    md = MarkdownPage(pb, fo, 'markdown', files)
    
    # Graph view integrations
    # ------------------------------------------------------------------
    # The nodelist will result in graph.json, which may have uses beyond the graph view

    # [17] Add self to nodelist
    node = pb.network_tree.NewNode()

    # add all metadata to node, so we can access it later when we need to, once compilation of html is complete
    node['metadata'] = md.metadata.copy()
    
    # Use filename as node id, unless 'graph_name' is set in the yaml frontmatter
    node['id'] = rel_dst_path.name.replace('.html', '')
    if 'graph_name' in md.metadata.keys():
        node['id'] = md.metadata['graph_name']

    # Url is used so you can open the note/node by clicking on it
    node['url'] = rel_dst_path.as_posix()
    pb.network_tree.AddNode(node)

    # Backlinks are set so when recursing, the links (edges) can be determined
    if backlinkNode is not None:
        link = pb.network_tree.NewLink()
        link['source'] = backlinkNode['id']
        link['target'] = node['id']
        pb.network_tree.AddLink(link)
    
    backlinkNode = node

    # Skip further processing if processing has happened already for this file
    # ------------------------------------------------------------------
    if fo.processed_mth == True:
        return

    if pb.gc('toggles/verbose_printout', cached=True):
        print('\t'*log_level, f"html: converting {page_path.as_posix()}")

    # [1] Replace code blocks with placeholders so they aren't altered
    # They will be restored at the end
    # ------------------------------------------------------------------
    md.StripCodeSections()     

    # Get all local markdown links. 
    # ------------------------------------------------------------------
    # This is any string in between '](' and  ')'
    proper_links = re.findall(r'(?<=\]\().+?(?=\))', md.page)
    for l in proper_links:
        # Init link
        link = MarkdownLink(pb, l, page_path, paths['md_folder'], url_unquote=True, relative_path_md = pb.gc('toggles/relative_path_md', cached=True))

        # Don't process in the following cases (link empty or // in the link)
        if link.isValid == False or link.isExternal == True: 
            continue

        # [12] Copy non md files over wholesale, then we're done for that kind of file
        if link.fo is None:
            if link.suffix != '.md' and '/obs.html/dir_index.html' not in link.url:
                print('\t'*(log_level+1), 'File ' + str(link.url) + ' not located, so not copied.')
        elif not link.fo.metadata['is_note'] and not link.fo.metadata['is_includable_file']:
            link.fo.copy_file('mth')
            
        # [13] Link to a custom 404 page when linked to a not-created note
        if link.name == 'not_created.md':
            new_link = f']({html_url_prefix}/not_created.html)'
        else:
            if link.fo is None:
                continue

            md.links.append(link.fo)

            # [11.1] Rewrite .md links to .html (when the link is to a file in our root folder)
            query_part = ''
            if link.query != '':
                query_part = link.query_delimiter + link.query 
            new_link = f']({link.fo.get_link("html", origin=fo)}{query_part})'
            
        # Update link
        safe_link = re.escape(']('+l+')')
        md.page = re.sub(safe_link, new_link, md.page)

    # [4] Handle local image links (copy them over to output)
    # ------------------------------------------------------------------
    for link in re.findall(r'\!\[.*\]\((.*?)\)', md.page):
        l = urllib.parse.unquote(link)
        if '://' in l:
            continue

        file_name = l.split('/')[-1]

        # Only handle local image files (images located in the root folder)
        # Doublecheck, who knows what some weird '../../folder/..' does...
        if file_name not in files.keys():
            if pb.gc('toggles/warn_on_skipped_image', cached=True):
                warnings.warn(f"Image {l} treated as external and not imported in html")
            continue
        
        lo = files[file_name]

        # Copy src to dst
        lo.copy_file('mth')

        # [11.2] Adjust image link in page to new dst folder (when the link is to a file in our root folder)
        new_link = '![]('+urllib.parse.quote(lo.get_link('html', origin=fo))+')'
        safe_link = r"\!\[.*\]\("+re.escape(link)+r"\)"
        md.page = re.sub(safe_link, new_link, md.page)

    # [?] Handle local source tag-links (copy them over to output)
    # ------------------------------------------------------------------
    for link in re.findall(r'(?<=<source src=")([^"]*)', md.page):
        l = urllib.parse.unquote(link)
        if '://' in l:
            continue
        file_name = l.split('/')[-1]

        # Only handle local video files (images located in the root folder)
        # Doublecheck, who knows what some weird '../../folder/..' does...
        if file_name not in files.keys():
            if pb.gc('toggles/warn_on_skipped_image', cached=True):
                warnings.warn(f"Media {l} treated as external and not imported in html")
            continue
        
        lo = files[file_name]

        # Copy src to dst
        lo.copy_file('mth')

        # [11.2] Adjust video link in page to new dst folder (when the link is to a file in our root folder)
        new_link = '<source src="'+urllib.parse.quote(lo.get_link('html', origin=fo))+'"'
        safe_link = r'<source src="'+re.escape(link)+r'"'
        md.page = re.sub(safe_link, new_link, md.page)

    # [?] Documentation styling: Table of Contents
    # ------------------------------------------------------------------
    if pb.gc('toggles/features/styling/add_toc', cached=True):
        if '[TOC]' not in md.page:
            md.page = '[TOC]\n' + md.page

    # [1] Restore codeblocks/-lines
    # ------------------------------------------------------------------
    md.RestoreCodeSections()

    # [11] Convert markdown to html
    # ------------------------------------------------------------------
    extension_configs = {
    'codehilite ': {
        'linenums': True
    }}
    html_body = markdown.markdown(md.page, extensions=['extra', 'codehilite', 'toc', 'obsidianhtml_md_mermaid_fork'], extension_configs=extension_configs)

    # HTML Tweaks
    # ------------------------------------------------------------------
    # [14] Tag external/anchor links with a class so they can be decorated differently
    for l in re.findall(r'(?<=\<a href=")([^"]*)', html_body):
        if l == '':
            continue

        # anchor links
        if l[0] == '#':
            new_str = f"<a href=\"{l}\" class=\"anchor-link\""
        
        # not internal or internal and not .html file
        elif (not l[0] in ('/','.')) or ('.' in l.split('/')[-1] and '.html' not in l.split('/')[-1]):
            # add in target="_blank" (or not)
            external_blank_html = ''
            if pb.gc('toggles/external_blank', cached=True):
                external_blank_html = 'target=\"_blank\" '

            new_str = f"<a href=\"{l}\" {external_blank_html}class=\"external-link\""
        else:
            continue
        
        # convert link
        safe_str = f"<a href=\"{l}\""
        html_body = html_body.replace(safe_str, new_str)

    # [15] Tag not created links with a class so they can be decorated differently
    html_body = html_body.replace(f'<a href="{html_url_prefix}/not_created.html">', f'<a href="{html_url_prefix}/not_created.html" class="nonexistent-link">')

    # [18] add backlinks to page 
    if pb.gc('toggles/features/backlinks/enabled', cached=True):
        html_body += '{_obsidian_html_backlinks_pattern_:'+node['id']+'}'    

    # [17] Add in graph code to template (via {content})
    # This shows the "Show Graph" button, and adds the js code to handle showing the graph
    if pb.gc('toggles/features/graph/enabled', cached=True):
        graph_template = OpenIncludedFile('graph/graph_template.html')
        graph_template = graph_template.replace('{id}', simpleHash(html_body))\
                                       .replace('{pinnedNode}', node['id'])\
                                       .replace('{html_url_prefix}', html_url_prefix)\
                                       .replace('{graph_coalesce_force}', pb.gc('toggles/features/graph/coalesce_force', cached=True))
        html_body += f"\n{graph_template}\n"

    # [16] Wrap body html in valid html structure from template
    # ------------------------------------------------------------------
    html = PopulateTemplate(pb, node['id'], pb.dynamic_inclusions, pb.html_template, content=html_body)

    # [?] Documentation styling: Navbar
    # ------------------------------------------------------------------
    html = html.replace('{pinnedNode}', node['id'])
    
    navbar_links = pb.gc('navbar_links', cached=True)
    elements = []
    for l in navbar_links:
        el = f'<a class="navbar-link"href="{html_url_prefix}/{l["link"]}" title="{l["name"]}">{l["name"]}</a>'
        elements.append(el)
    html = html.replace('{{navbar_links}}', '\n'.join(elements))  

    # Save file
    # ------------------------------------------------------------------
    fo.path['html']['file_absolute_path'].parent.mkdir(parents=True, exist_ok=True)   
    html_dst_path_posix = fo.path['html']['file_absolute_path'].as_posix()

    md.AddToTagtree(pb.tagtree, fo.path['html']['file_relative_path'].as_posix())

    # Write html
    with open(html_dst_path_posix, 'w', encoding="utf-8") as f:
        f.write(html)

    # Set file to processed
    fo.processed_mth = True

    # > Done with this markdown page!

    # Recurse for every link in the current page
    # ------------------------------------------------------------------
    for lo in md.links:
        if not lo.is_valid_note('markdown'):
            continue

        # Convert the note that is linked to
        if pb.gc('toggles/verbose_printout', cached=True):
            print('\t'*(log_level+1), f"html: initiating conversion for {lo.fullpath('markdown')} (parent {fo.fullpath('markdown')})")

        ConvertMarkdownPageToHtmlPage(lo, pb, backlinkNode, log_level=log_level)

def recurseTagList(tagtree, tagpath, pb, level):
    '''This function creates the folder `tags` in the html_output_folder, and a filestructure in that so you can navigate the tags.'''

    # Get relevant paths
    # ---------------------------------------------------------
    tags_folder = pb.paths['html_output_folder'].joinpath('obs.html/tags/')
    tag_dst_path = tags_folder.joinpath(f'{tagpath}index.html').resolve()
    tag_dst_path_posix = tag_dst_path.as_posix()
    rel_dst_path_as_posix = tag_dst_path.relative_to(pb.paths['html_output_folder']).as_posix()

    html_url_prefix = pb.gc('html_url_prefix')
    if pb.gc('toggles/relative_path_html', cached=True):
        html_url_prefix = pb.sc(path='html_url_prefix', value=get_rel_html_url_prefix(rel_dst_path_as_posix))

    # Make root dir
    tags_folder.mkdir(parents=True, exist_ok=True)

    # Compile markdown from tagtree
    # ---------------------------------------------------------
    md = ''
    # Handle subtags
    if len(tagtree['subtags'].keys()) > 0:
        if level == 0:
            md += '# Tags\n'
        else:
            md += '# Subtags\n'

        for key in tagtree['subtags'].keys():
            # Point of recursion
            rel_key_path_as_posix = recurseTagList(tagtree['subtags'][key], tagpath + key + '/', pb, level+1)
            md += f'- [{key}]({html_url_prefix}/{rel_key_path_as_posix})' + '\n'

    # Handle notes
    if len(tagtree['notes']) > 0:
        md += '\n# Notes\n'
        for note_url in tagtree['notes']:
            note_name = note_url.split('/')[-1].replace(".html", "")
            md += f'- [{note_name}]({html_url_prefix}/{note_url})\n'

    # Compile html
    html_body = markdown.markdown(md, extensions=['extra', 'codehilite', 'toc', 'obsidianhtml_md_mermaid_fork'])

    di = '<link rel="stylesheet" href="'+html_url_prefix+'/obs.html/static/taglist.css" />'

    html = PopulateTemplate(pb, 'none', pb.dynamic_inclusions, pb.html_template, html_url_prefix=html_url_prefix, content=html_body, dynamic_includes=di, container_wrapper_class_list=['single_tab_page-left-aligned'])


    html = html.replace('{pinnedNode}', 'tagspage')

    navbar_links = pb.gc('navbar_links', cached=True)
    elements = []
    for l in navbar_links:
        el = f'<a class="navbar-link"href="{html_url_prefix}/{l["link"]}" title="{l["name"]}">{l["name"]}</a>'
        elements.append(el)
    html = html.replace('{{navbar_links}}', '\n'.join(elements)) 
    
    # Write file
    tag_dst_path.parent.mkdir(parents=True, exist_ok=True)   
    with open(tag_dst_path_posix, 'w', encoding="utf-8") as f:
        f.write(html) 

    # Return link of this page, to be used by caller for building its page
    return rel_dst_path_as_posix

def simpleHash(text:str):
    hash=0
    for ch in text:
        hash = ( hash*281  ^ ord(ch)*997) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
    return str(hash)


def main():
    # Show help text
    # ---------------------------------------------------------
    if '-h' in sys.argv:
        printHelpAndExit(0)

    # Make "global" object that we can pass to functions
    # ---------------------------------------------------------
    pb = PicknickBasket()

    # Export packaged html template so users can edit it and then use their custom template
    # ---------------------------------------------------------
    export_html_template_target_path = None
    for i, v in enumerate(sys.argv):
        if v == '-eht':
            if len(sys.argv) < (i + 2):
                print(f'No output path given.\n  Use `obsidianhtml -eht /target/path/to/template.html <documentation/tabs/no_tabs>` to provide input.')
                printHelpAndExit(1)
            if len(sys.argv) < (i + 3):
                print(f'No layout name given.\n  Use `obsidianhtml -eht /target/path/to/template.html <documentation/tabs/no_tabs>` to provide input.')
                printHelpAndExit(1)
            if sys.argv[i+2] not in ['documentation', 'tabs', 'no_tabs']:
                print(f'Provided layout name of {sys.argv[i+2]} is unknown.\n  Use `obsidianhtml -eht /target/path/to/template.html <documentation/tabs/no_tabs>` to provide input.')
                printHelpAndExit(1)

            export_html_template_target_path = Path(sys.argv[i+1]).resolve()
            export_html_template_target_path.parent.mkdir(parents=True, exist_ok=True)
            html = OpenIncludedFile(f'html/template_{sys.argv[i+2]}.html')

            with open (export_html_template_target_path, 'w', encoding="utf-8") as t:
                t.write(html)
            print(f"Exported html template to {str(export_html_template_target_path)}")
            exit(0)


    # Export packaged default config so users can see what is default behavior
    # ---------------------------------------------------------
    for i, v in enumerate(sys.argv):
        if v == '-gc':
            default_config = OpenIncludedFile('defaults_config.yml')
            print(default_config)
            exit(0)

    # Other commandline arguments
    # ---------------------------------------------------------
    # Set verbosity (overwrite config)
    for i, v in enumerate(sys.argv):
        if v == '-v':
            pb.verbose = True
            break

    # Set config
    input_yml_path_str = 'config.yml'
    for i, v in enumerate(sys.argv):
        if v == '-i':
            if len(sys.argv) < (i + 2):
                print(f'No config path given.\n  Use `obsidianhtml -i /target/path/to/config.yml` to provide input.')
                printHelpAndExit(1)            
            input_yml_path_str = sys.argv[i+1]
            break

    pb.loadConfig(input_yml_path_str)


    # Set Paths
    # ---------------------------------------------------------
    paths = {
        'obsidian_folder': Path(pb.gc('obsidian_folder_path_str')).resolve(),
        'md_folder': Path(pb.gc('md_folder_path_str')).resolve(),
        'obsidian_entrypoint': Path(pb.gc('obsidian_entrypoint_path_str')).resolve(),
        'md_entrypoint': Path(pb.gc('md_entrypoint_path_str')).resolve(),
        'html_output_folder': Path(pb.gc('html_output_folder_path_str')).resolve()
    }
    if pb.gc('toggles/extended_logging', cached=True):
        paths['log_output_folder'] = Path(pb.gc('log_output_folder_path_str')).resolve()

    # Deduce relative paths
    paths['rel_obsidian_entrypoint'] = paths['obsidian_entrypoint'].relative_to(paths['obsidian_folder'])
    paths['rel_md_entrypoint_path']  = paths['md_entrypoint'].relative_to(paths['md_folder'])


    # Features/Toggles influencing other settings
    # ------------------------------------------------------------------
    
    # if pb.gc('toggles/relative_path_html', cached=True):
    #     # Disable graph view
    #     if pb.gc('toggles/features/graph/enabled'):
    #         print(f"WARNING: disabling graph view - not supported with setting relative_path_html:True")
    #         pb.config.disable_feature('graph')

    #     # Enable no tab
    #     if pb.gc('toggles/no_tabs') == False:
    #         print(f"WARNING: enabling setting no_tabs - tabbing not supported with relative_path_html:True")
    #         pb.sc(path='toggles/no_tabs', value=True)

    # Copy vault to tempdir, so any bugs will not affect the user's vault
    # ---------------------------------------------------------
    if pb.gc('copy_vault_to_tempdir'):
        # Copy over vault to tempdir
        tmpdir = CreateTemporaryCopy(source_folder_path=paths['obsidian_folder'], pb=pb)

        # update paths
        paths['original_obsidian_folder'] = paths['obsidian_folder']        # use only for lookups!
        paths['obsidian_folder'] = Path(tmpdir.name).resolve()
        paths['obsidian_entrypoint'] = paths['obsidian_folder'].joinpath(paths['rel_obsidian_entrypoint'])
    else:
        paths['original_obsidian_folder'] = paths['obsidian_folder']        # use only for lookups!

    # Add paths to pb
    # ---------------------------------------------------------
    pb.paths = paths

    # Compile dynamic inclusion list
    # ---------------------------------------------------------
    # This is a set of javascript/css files to be loaded into the header based on config choices.
    dynamic_inclusions = ""
    try:
        dynamic_inclusions += '\n'.join(pb.gc('html_custom_inclusions')) +'\n'
    except:
        None
    pb.dynamic_inclusions = dynamic_inclusions


    # Remove potential previous output
    # ---------------------------------------------------------
    if pb.gc('toggles/no_clean', cached=True) == False:
        print('> CLEARING OUTPUT FOLDERS')
        if pb.gc('toggles/compile_md', cached=True):
            if paths['md_folder'].exists():
                shutil.rmtree(paths['md_folder'])

        if paths['html_output_folder'].exists():
            shutil.rmtree(paths['html_output_folder'])    

    # Create folder tree
    # ---------------------------------------------------------
    print('> CREATING OUTPUT FOLDERS')
    paths['md_folder'].mkdir(parents=True, exist_ok=True)
    paths['md_folder'] = paths['md_folder'].resolve()

    paths['html_output_folder'].mkdir(parents=True, exist_ok=True)
    paths['html_output_folder'] = paths['html_output_folder'].resolve()
    
    if pb.gc('toggles/extended_logging', cached=True):
        paths['log_output_folder'].mkdir(parents=True, exist_ok=True)
        paths['log_output_folder'] = paths['log_output_folder'].resolve()

    # Load files
    # ---------------------------------------------------------
    input_dir = paths['obsidian_folder']
    path_type = 'note'
    if not pb.gc('toggles/compile_md'):
        input_dir = paths['md_folder']
        path_type = 'markdown'

    # Load all filenames in the root folder.
    # This data will be used to check which files are local, and to get their full path
    # It's clear that no two files can be allowed to have the same file name.
    if pb.gc('toggles/verbose_printout'):
        print('> CREATING FILE TREE')
    pb.files = {}
    for path in input_dir.rglob('*'):
        if path.is_dir():
            continue

        # Exclude configured subfolders
        try:
            _continue = False
            for folder in pb.gc('exclude_subfolders', cached=True):
                excl_folder_path = input_dir.joinpath(folder)
                if path.resolve().is_relative_to(excl_folder_path):
                    if pb.gc('toggles/verbose_printout', cached=True):
                        print(f'\tExcluded folder {excl_folder_path}: Excluded file {path.name}.')
                    _continue = True
                    break
            if _continue:
                continue
        except:
            None

        # Check if filename is duplicate
        if path.name in pb.files.keys() and pb.gc('toggles/allow_duplicate_filenames_in_root', cached=True) == False:
            raise DuplicateFileNameInRoot(f"Two or more files with the name \"{path.name}\" exist in the root folder. See {str(path)} and {pb.files[path.name].path[path_type]['file_absolute_path']}.")

        # Create object to help with handling all the info on the file
        fo = OH_File(pb)

        # Compile paths
        if pb.gc('toggles/compile_md', cached=True):
            # compile note --> markdown
            fo.init_note_path(path)
            fo.compile_metadata(fo.path['note']['file_absolute_path'], cached=True)

            if pb.gc('toggles/compile_html', cached=True):
                # compile markdown --> html (based on the given note path)
                fo.init_markdown_path()
                fo.compile_metadata(fo.path['markdown']['file_absolute_path'], cached=True)
        else:
            # compile markdown --> html (based on the found markdown path)
            fo.init_markdown_path(path)
            fo.compile_metadata(fo.path['markdown']['file_absolute_path'], cached=True)

        # Add to tree
        pb.files[path.name] = fo

    if pb.gc('toggles/verbose_printout', cached=True):
        print('< CREATING FILE TREE: Done')

    if pb.gc('toggles/extended_logging', cached=True):
        WriteFileLog(pb.files, paths['log_output_folder'].joinpath('files.md'), include_processed=False)

    # Convert Obsidian to markdown
    # ---------------------------------------------------------
    if pb.gc('toggles/compile_md', cached=True):

        # Create index.md based on given tagnames, that will serve as the entrypoint
        # ---------------------------------------------------------
        if pb.gc('toggles/features/create_index_from_tags/enabled'):
            pb = CreateIndexFromTags(pb)

        # Start conversion with entrypoint.
        # ---------------------------------------------------------
        # Note: this will mean that any note not (indirectly) linked by the entrypoint will not be included in the output!
        print(f'> COMPILING MARKDOWN FROM OBSIDIAN CODE ({str(paths["obsidian_entrypoint"])})')
        ep = pb.files[paths['obsidian_entrypoint'].name]
        recurseObisidianToMarkdown(ep, pb)


        # Keep going until all other files are processed
        if pb.gc('toggles/process_all', cached=True):
            print('\t> FEATURE: PROCESS ALL')
            unparsed = [x for x in pb.files.values() if x.processed_ntm == False]
            i = 0
            l = len(unparsed)
            for fo in unparsed:
                i += 1
                if pb.gc('toggles/verbose_printout', cached=True) == True:
                    print(f'\t\t{i}/{l} - ' + str(fo.path['note']['file_absolute_path']))
                recurseObisidianToMarkdown(fo, pb, log_level=2)
            print('\t< FEATURE: PROCESS ALL: Done')

    if pb.gc('toggles/extended_logging', cached=True):
        WriteFileLog(pb.files, paths['log_output_folder'].joinpath('files_ntm.md'), include_processed=True)


    # Convert Markdown to Html
    # ------------------------------------------
    if pb.gc('toggles/compile_html', cached=True):
        print(f'> COMPILING HTML FROM MARKDOWN CODE ({str(paths["md_entrypoint"])})')

        # Get html template code. 
        # Every note will become a html page, where the body comes from the note's markdown, 
        # and the wrapper code from this template.
        try:
            with open(Path(pb.gc('html_template_path_str')).resolve()) as f:
                html_template = f.read()
        except:
            layout = pb.gc('toggles/features/styling/layout')
            html_template = OpenIncludedFile(f'html/template_{layout}.html')

        if '{content}' not in html_template:
            raise Exception('The provided html template does not contain the string `{content}`. This will break its intended use as a template.')
            exit(1)

        pb.html_template = html_template
        
        # Start conversion from the entrypoint
        ep = pb.files[paths['md_entrypoint'].name]
        ConvertMarkdownPageToHtmlPage(ep, pb)
        
        # Keep going until all other files are processed
        if pb.gc('toggles/process_all') == True:
            print('\t> FEATURE: PROCESS ALL')
            unparsed = [x for x in pb.files.values() if x.processed_mth == False]
            i = 0; l = len(unparsed)
            for fo in unparsed:
                i += 1
                if pb.gc('toggles/verbose_printout', cached=True) == True:
                    print(f'\t\t{i}/{l} - ' + str(fo.path['markdown']['file_absolute_path']))

                ConvertMarkdownPageToHtmlPage(fo, pb, log_level=2)
            print('\t< FEATURE: PROCESS ALL: Done')

        if pb.gc('toggles/extended_logging', cached=True):
            WriteFileLog(pb.files, paths['log_output_folder'].joinpath('files_mth.md'), include_processed=True)


        # [18] Add in backlinks
        # ------------------------------------------
        if pb.gc('toggles/features/backlinks/enabled'):
            # Make lookup so that we can easily find the url of a node
            pb.network_tree.compile_node_lookup()

            for fo in pb.files.values():
                if not fo.metadata['is_note']:
                    continue

                # get paths / html prefix
                dst_abs_path = fo.path['html']['file_absolute_path']
                dst_rel_path_str = fo.path['html']['file_relative_path'].as_posix()
                html_url_prefix = get_html_url_prefix(pb, rel_path_str=dst_rel_path_str)

                # get html content
                try:
                    with open(dst_abs_path, 'r', encoding="utf-8") as f:
                        html = f.read()
                except:
                    continue
                
                # Get node_id
                m = re.search(r'(?<=\{_obsidian_html_backlinks_pattern_:)(.*?)(?=\})', html)
                if m is None:
                    continue
                node_id = m.group(0)

                # Compile backlinks list
                backlinks = [x for x in pb.network_tree.tree['links'] if x['target'] == node_id]
                snippet = ''
                if len(backlinks) > 0:
                    snippet = "<h2>Backlinks</h2>\n<ul>\n"
                    for l in backlinks:
                        if l['target'] == node_id:
                            url = pb.network_tree.node_lookup[l['source']]['url']
                            if url[0] != '/':
                                url = '/'+url
                            snippet += f'\t<li><a class="backlink" href="{url}">{l["source"]}</a></li>\n'
                    snippet += '</ul>'

                # replace placeholder with list & write output
                html = re.sub('\{_obsidian_html_backlinks_pattern_:'+re.escape(node_id)+'}', snippet, html)
                with open(dst_abs_path, 'w', encoding="utf-8") as f:
                    f.write(html)

        # Create tag page
        recurseTagList(pb.tagtree, '', pb, level=0)

        # Add Extra stuff to the output directories
        ExportStaticFiles(pb)

        # Write node json to static folder
        with open (pb.paths['html_output_folder'].joinpath('obs.html').joinpath('data/graph.json'), 'w', encoding="utf-8") as f:
            f.write(pb.network_tree.OutputJson())

    print('< COMPILING HTML FROM MARKDOWN CODE: Done')

    if pb.gc('toggles/features/rss/enabled'):
        print('> COMPILING RSS FEED')
        feed = RssFeed(pb)
        feed.Compile()
        print('< COMPILING RSS FEED: Done')

    if pb.gc('toggles/features/create_index_from_dir_structure/enabled'):
        rel_output_path = pb.gc('toggles/features/create_index_from_dir_structure/rel_output_path')
        op = paths['html_output_folder'].joinpath(rel_output_path)

        print(f'> COMPILING INDEX FROM DIR STRUCTURE ({op})')
        treeobj = CreateIndexFromDirStructure(pb, pb.paths['html_output_folder'])
        treeobj.BuildIndex()
        treeobj.WriteIndex()
        print('< COMPILING INDEX FROM DIR STRUCTURE: Done')


