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

from .MarkdownPage import MarkdownPage
from .MarkdownLink import MarkdownLink
from .lib import    DuplicateFileNameInRoot, CreateTemporaryCopy, \
                    GetObsidianFilePath, OpenIncludedFile, ExportStaticFiles, \
                    IsValidLocalMarkdownLink, PopulateTemplate, \
                    printHelpAndExit
from .PicknickBasket import PicknickBasket

from .CreateIndexFromTags import CreateIndexFromTags
from .CreateIndexFromDirStructure import CreateIndexFromDirStructure
from .RssFeed import RssFeed

# Open source files in the package
import importlib.resources as pkg_resources
import importlib.util
from . import src


def recurseObisidianToMarkdown(page_path_str, pb, log_level=1):
    '''This functions converts an obsidian note to a markdown file and calls itself on any local note links it finds in the page.'''

    # Unpack picknick basket so we don't have to type too much.
    paths = pb.paths        # Paths of interest, such as the output and input folders
    files = pb.files        # Hashtable of all files found in the obsidian vault

    # Convert path string to Path and do a double check
    page_path = Path(page_path_str).resolve()
    if page_path.exists() == False:
        return
    if page_path.suffix != '.md':
        return

    # Convert note to markdown
    # ------------------------------------------------------------------
    # Create an object that handles a lot of the logic of parsing the page paths, content, etc
    md = MarkdownPage(page_path, paths['obsidian_folder'], files)

    # The bulk of the conversion process happens here
    md.ConvertObsidianPageToMarkdownPage(pb, paths['md_folder'], paths['obsidian_entrypoint'])

    # The frontmatter was stripped from the obsidian note prior to conversion
    # Add yaml frontmatter back in
    md.page = (frontmatter.dumps(frontmatter.Post("", **md.metadata))) + '\n' + md.page

    # Save file
    # ------------------------------------------------------------------
    # Create folder if necessary
    md.dst_path.parent.mkdir(parents=True, exist_ok=True)

    # Write markdown to file
    with open(md.dst_path, 'w', encoding="utf-8") as f:
        f.write(md.page)

    # Recurse for every link in the current page
    # ------------------------------------------------------------------
    for l in md.links:
        link = GetObsidianFilePath(l, files)
        if link[1] == False or link[1]['processed'] == True:
            if pb.gc('toggles','verbose_printout'):
                if link[1] == False:
                    print('\t'*log_level, f"Skipping converting {l}, link not internal or not valid.")
                else:
                    print('\t'*log_level, f"Skipping converting {l}, already processed.")
            continue
        link_path = link[0]

        # Mark the file as processed so that it will not be processed again at a later stage
        files[link_path]['processed'] = True         

        # Convert the note that is linked to
        if pb.gc('toggles','verbose_printout'):
            print('\t'*log_level, f"found link {files[link_path]['fullpath']} (through parent {page_path})")

        recurseObisidianToMarkdown(files[link_path]['fullpath'], pb, log_level=log_level)

def ConvertMarkdownPageToHtmlPage(page_path_str, pb, backlinkNode=None, log_level=1):
    '''This functions converts a markdown page to an html file and calls itself on any local markdown links it finds in the page.'''
    
    # Unpack picknick basket so we don't have to type too much.
    paths = pb.paths                    # Paths of interest, such as the output and input folders
    files = pb.files                    # Hashtable of all files found in the obsidian vault

    # Convert path string to Path and do a double check
    page_path = Path(page_path_str).resolve()
    if not IsValidLocalMarkdownLink(page_path_str):
        return

    # Load contents
    # ------------------------------------------------------------------
    # Create an object that handles a lot of the logic of parsing the page paths, content, etc
    md = MarkdownPage(page_path, paths['md_folder'], files)
    md.SetDestinationPath(paths['html_output_folder'], paths['md_entrypoint'])

    # Fix the issue of a note being called 'index.md' in the root folder
    if md.dst_path == paths['html_output_folder'].joinpath('index.md') and md.src_path != paths['md_entrypoint']:
        md.dst_path = md.dst_path.parent.joinpath('index__2.md')
        md.rel_dst_path = md.dst_path.relative_to(md.dst_folder_path)
    

    # Graph view integrations
    # ------------------------------------------------------------------
    # The nodelist will result in graph.json, which may have uses beyond the graph view

    # [17] Add self to nodelist
    node = pb.network_tree.NewNode()

    # add all metadata to node, so we can access it later when we need to, once compilation of html is complete
    node['metadata'] = md.metadata.copy()
    
    # Use filename as node id, unless 'graph_name' is set in the yaml frontmatter
    node['id'] = md.rel_dst_path.as_posix().split('/')[-1].replace('.md', '')
    if 'graph_name' in md.metadata.keys():
        node['id'] = md.metadata['graph_name']

    # Url is used so you can open the note/node by clicking on it
    node['url'] = f'{pb.gc("html_url_prefix")}/{md.rel_dst_path.as_posix()[:-3]}.html'
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
    if files[md.rel_src_path.as_posix()]['processed'] == True:
        return

    if pb.gc('toggles','verbose_printout'):
        print('\t'*log_level, f"html: converting {page_path.as_posix()} (parent {md.src_path})")

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
        link = MarkdownLink(l, page_path, paths['md_folder'], url_unquote=True, relative_path_md = pb.gc('toggles','relative_path_md'))

        # Don't process in the following cases
        if link.isValid == False or link.isExternal == True: 
            continue

        # [12] Copy non md files over wholesale, then we're done for that kind of file
        if link.suffix != '.md' and link.suffix not in pb.gc('included_file_suffixes'):
            paths['html_output_folder'].joinpath(link.rel_src_path).parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copyfile(link.src_path, paths['html_output_folder'].joinpath(link.rel_src_path))
            except FileNotFoundError:
                print('\t'*(log_level+1), 'File ' + str(link.src_path) + ' not located, so not copied.')
            continue

        # [13] Link to a custom 404 page when linked to a not-created note
        if link.url.split('/')[-1] == 'not_created.md':
            new_link = f']({pb.gc("html_url_prefix")}/not_created.html)'
        else:
            if link.rel_src_path_posix not in files.keys():
                continue

            md.links.append(link.rel_src_path_posix)

            # [11.1] Rewrite .md links to .html (when the link is to a file in our root folder)
            query_part = ''
            if link.query != '':
                query_part = link.query_delimiter + link.query 
            new_link = f']({pb.gc("html_url_prefix")}/{link.rel_src_path_posix[:-3]}.html{query_part})'
            
        # Update link
        safe_link = re.escape(']('+l+')')
        md.page = re.sub(safe_link, new_link, md.page)

    # [4] Handle local image links (copy them over to output)
    # ------------------------------------------------------------------
    for link in re.findall(r'\!\[.*\]\((.*?)\)', md.page):
        l = urllib.parse.unquote(link)
        if '://' in l:
            continue
        full_link_path = page_path.parent.joinpath(l).resolve()
        rel_path = full_link_path.relative_to(paths['md_folder'])

        # Only handle local image files (images located in the root folder)
        # Doublecheck, who knows what some weird '../../folder/..' does...
        if rel_path.as_posix() not in files.keys():
            if pb.gc('toggles','warn_on_skipped_image'):
                warnings.warn(f"Image {str(full_link_path)} treated as external and not imported in html")
            continue

        # Copy src to dst
        dst_path = paths['html_output_folder'].joinpath(rel_path)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(full_link_path, dst_path)

        # [11.2] Adjust image link in page to new dst folder (when the link is to a file in our root folder)
        new_link = '![]('+urllib.parse.quote(pb.gc('html_url_prefix')+'/'+rel_path.as_posix())+')'
        safe_link = r"\!\[.*\]\("+re.escape(link)+r"\)"
        md.page = re.sub(safe_link, new_link, md.page)

    # [?] Handle local source tag-links (copy them over to output)
    # ------------------------------------------------------------------
    for link in re.findall(r'(?<=<source src=")([^"]*)', md.page):
        l = urllib.parse.unquote(link)
        if '://' in l:
            continue
        full_link_path = page_path.parent.joinpath(l).resolve()
        rel_path = full_link_path.relative_to(paths['md_folder'])

        # Only handle local video files (images located in the root folder)
        # Doublecheck, who knows what some weird '../../folder/..' does...
        if rel_path.as_posix() not in files.keys():
            if pb.gc('toggles','warn_on_skipped_image'):
                warnings.warn(f"Video {str(full_link_path)} treated as external and not imported in html")
            continue

        # Copy src to dst
        dst_path = paths['html_output_folder'].joinpath(rel_path)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(full_link_path, dst_path)

        # [11.2] Adjust video link in page to new dst folder (when the link is to a file in our root folder)
        new_link = '<source src="'+urllib.parse.quote(pb.gc('html_url_prefix')+'/'+rel_path.as_posix())+'"'
        safe_link = r'<source src="'+re.escape(link)+r'"'
        md.page = re.sub(safe_link, new_link, md.page)


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
        if l[0] == '/':
            # Internal link, skip
            continue

        # anchor links
        if l[0] == '#':
            new_str = f"<a href=\"{l}\" class=\"anchor-link\""
        
        # external links
        else:
            # add in target="_blank" (or not)
            external_blank_html = ''
            if pb.gc('toggles','external_blank'):
                external_blank_html = 'target=\"_blank\" '

            new_str = f"<a href=\"{l}\" {external_blank_html}class=\"external-link\""
        
        # convert link
        safe_str = f"<a href=\"{l}\""
        html_body = html_body.replace(safe_str, new_str)

    # [15] Tag not created links with a class so they can be decorated differently
    html_body = html_body.replace(f'<a href="{pb.gc("html_url_prefix")}/not_created.html">', f'<a href="{pb.gc("html_url_prefix")}/not_created.html" class="nonexistent-link">')

    # [18] add backlinks to page 
    if pb.gc('toggles','features','backlinks','enabled'):
        html_body += '{_obsidian_html_backlinks_pattern_:'+node['id']+'}'    

    # [17] Add in graph code to template (via {content})
    # This shows the "Show Graph" button, and adds the js code to handle showing the graph
    if pb.gc('toggles','features','graph','enabled'):
        graph_template = OpenIncludedFile('graph/graph_template.html')
        graph_template = graph_template.replace('{id}', simpleHash(html_body))\
                                       .replace('{pinnedNode}', node['id'])\
                                       .replace('{html_url_prefix}', pb.gc('html_url_prefix'))\
                                       .replace('{graph_coalesce_force}', pb.gc('toggles','features','graph','coalesce_force'))
        html_body += f"\n{graph_template}\n"

    # [16] Wrap body html in valid html structure from template
    # ------------------------------------------------------------------
    html = PopulateTemplate(pb, node['id'], pb.gc('site_name'), pb.gc('html_url_prefix'), pb.dynamic_inclusions, pb.html_template, content=html_body)

    # Save file
    # ------------------------------------------------------------------
    md.dst_path.parent.mkdir(parents=True, exist_ok=True)   
    html_dst_path_posix = md.dst_path.as_posix()[:-3] + '.html' 

    md.AddToTagtree(pb.tagtree, md.dst_path.relative_to(paths['html_output_folder']).as_posix()[:-3] + '.html')

    # Write html
    with open(html_dst_path_posix, 'w', encoding="utf-8") as f:
        f.write(html)

    # Set file to processed
    files[md.rel_src_path.as_posix()]['processed'] = True

    # > Done with this markdown page!

    # Recurse for every link in the current page
    # ------------------------------------------------------------------
    for l in md.links:
        # these are of type rel_path_posix
        link_path = l
        
        # Skip non-existent links
        if link_path not in files.keys():
            continue

        if not IsValidLocalMarkdownLink(files[link_path]['fullpath']):
            continue

        # Convert the note that is linked to
        if pb.gc('toggles','verbose_printout'):
            print('\t'*(log_level+1), f"html: initiating conversion for {files[link_path]['fullpath']} (parent {md.src_path})")

        ConvertMarkdownPageToHtmlPage(files[link_path]['fullpath'], pb, backlinkNode, log_level=log_level)

def recurseTagList(tagtree, tagpath, pb, level):
    '''This function creates the folder `tags` in the html_output_folder, and a filestructure in that so you can navigate the tags.'''

    # Get relevant paths
    # ---------------------------------------------------------
    html_url_prefix = pb.gc('html_url_prefix')
    tags_folder = pb.paths['html_output_folder'].joinpath('obs.html/tags/')
    tag_dst_path = tags_folder.joinpath(f'{tagpath}index.html').resolve()
    tag_dst_path_posix = tag_dst_path.as_posix()
    rel_dst_path_as_posix = tag_dst_path.relative_to(pb.paths['html_output_folder']).as_posix()

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
        for note in tagtree['notes']:
            md += f'- [{note.replace(".html", "")}]({html_url_prefix}/{note})\n'

    # Compile html
    html_body = markdown.markdown(md, extensions=['extra', 'codehilite', 'toc', 'obsidianhtml_md_mermaid_fork'])

    di = '<link rel="stylesheet" href="'+pb.gc('html_url_prefix')+'/obs.html/static/taglist.css" />'
    html = PopulateTemplate(pb, 'none', pb.gc('site_name'), pb.gc('html_url_prefix'), pb.dynamic_inclusions, pb.html_template, content=html_body, dynamic_includes=di)

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
                print(f'No output path given.\n  Use `obsidianhtml -eht /target/path/to/template.html` to provide input.')
                printHelpAndExit(1)
            export_html_template_target_path = Path(sys.argv[i+1]).resolve()
            export_html_template_target_path.parent.mkdir(parents=True, exist_ok=True)
            html = OpenIncludedFile('html/template.html')
            with open (export_html_template_target_path, 'w', encoding="utf-8") as t:
                t.write(html)
            print(f"Exported html template to {str(export_html_template_target_path)}.")
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

    # Deduce relative paths
    paths['rel_obsidian_entrypoint'] = paths['obsidian_entrypoint'].relative_to(paths['obsidian_folder'])
    paths['rel_md_entrypoint_path']  = paths['md_entrypoint'].relative_to(paths['md_folder'])


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

    if pb.gc('toggles','features','graph','enabled'):
        dynamic_inclusions += '<link rel="stylesheet" href="'+pb.gc('html_url_prefix')+'/obs.html/static/graph.css" />' + "\n"
        dynamic_inclusions += '<script src="https://d3js.org/d3.v4.min.js"></script>' + "\n"

    if pb.gc('toggles','features','create_index_from_dir_structure','enabled'):
        dynamic_inclusions += '<script src="'+pb.gc('html_url_prefix')+'/obs.html/static/dirtree.js" /></script>' + "\n"


    # Remove potential previous output
    # ---------------------------------------------------------
    if pb.gc('toggles','no_clean') == False:
        print('> CLEARING OUTPUT FOLDERS')
        if pb.gc('toggles','compile_md'):
            if paths['md_folder'].exists():
                shutil.rmtree(paths['md_folder'])

        if paths['html_output_folder'].exists():
            shutil.rmtree(paths['html_output_folder'])    

    # Create folder tree
    # ---------------------------------------------------------
    print('> CREATING OUTPUT FOLDERS')
    paths['md_folder'].mkdir(parents=True, exist_ok=True)
    paths['html_output_folder'].mkdir(parents=True, exist_ok=True)


    # Convert Obsidian to markdown
    # ---------------------------------------------------------
    if pb.gc('toggles','compile_md'):

        # Load all filenames in the root folder.
        # This data will be used to check which files are local, and to get their full path
        # It's clear that no two files can be allowed to have the same file name.
        if pb.gc('toggles','verbose_printout'):
            print('> CREATING FILE TREE')
        files = {}
        for path in paths['obsidian_folder'].rglob('*'):
            if path.is_dir():
                continue

            # Exclude configured subfolders
            try:
                _continue = False
                for folder in pb.gc('exclude_subfolders'):
                    excl_folder_path = paths['obsidian_folder'].joinpath(folder)
                    if path.resolve().is_relative_to(excl_folder_path):
                        if pb.gc('toggles','verbose_printout'):
                            print(f'\tExcluded folder {excl_folder_path}: Excluded file {path.name}.')
                        _continue = True
                        break
                if _continue:
                    continue
            except:
                None

            # Check if filename is duplicate
            if path.name in files.keys() and pb.gc('toggles','allow_duplicate_filenames_in_root') == False:
                print(path)
                raise DuplicateFileNameInRoot(f"Two or more files with the name \"{path.name}\" exist in the root folder. See {str(path)} and {files[path.name]['fullpath']}.")

            # Fetch creation_time/modified_time from orginal location
            rel_path = path.relative_to(paths['obsidian_folder'])
            original_path = paths['original_obsidian_folder'].joinpath(rel_path)

            creation_time = None
            modified_time = None
            if platform.system() == 'Windows' or platform.system() == 'Darwin':
                creation_time = datetime.datetime.fromtimestamp(os.path.getctime(original_path)).isoformat()
                modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(original_path)).isoformat()
            else:
                modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(original_path)).isoformat()

            # Add to tree
            files[path.name] = {'fullpath': str(path), 'processed': False, 'pathobj': path, 'creation_time': creation_time, 'modified_time': modified_time}  

        pb.files = files

        if pb.gc('toggles','verbose_printout'):
            print('< CREATING FILE TREE: Done')

        # Create index.md based on given tagnames, that will serve as the entrypoint
        # ---------------------------------------------------------
        if pb.gc('toggles','features','create_index_from_tags','enabled'):
            pb = CreateIndexFromTags(pb)


        # Start conversion with entrypoint.
        # ---------------------------------------------------------
        # Note: this will mean that any note not (indirectly) linked by the entrypoint will not be included in the output!
        print(f'> COMPILING MARKDOWN FROM OBSIDIAN CODE ({str(paths["obsidian_entrypoint"])})')
        recurseObisidianToMarkdown(str(paths['obsidian_entrypoint']), pb)

        # Keep going until all other files are processed
        if pb.gc('toggles','process_all'):
            print('\t> FEATURE: PROCESS ALL')
            unparsed = {}
            for k in files.keys():
                if files[k]["processed"] == False:
                    unparsed[k] = files[k]

            i = 0
            l = len(unparsed.keys())
            for k in unparsed.keys():
                i += 1
                if pb.gc('toggles','verbose_printout') == True:
                    print(f'\t\t{i}/{l} - ' + unparsed[k]['fullpath'])
                recurseObisidianToMarkdown(unparsed[k]['fullpath'], pb, log_level=2)
            print('\t< FEATURE: PROCESS ALL: Done')


    # Convert Markdown to Html
    # ------------------------------------------
    if pb.gc('toggles','compile_html'):
        print(f'> COMPILING HTML FROM MARKDOWN CODE ({str(paths["md_entrypoint"])})')

        # Get html template code. 
        # Every note will become a html page, where the body comes from the note's markdown, 
        # and the wrapper code from this template.
        try:
            with open(Path(pb.gc('html_template_path_str')).resolve()) as f:
                html_template = f.read()
        except:
            html_template = OpenIncludedFile('html/template.html')

        if '{content}' not in html_template:
            raise Exception('The provided html template does not contain the string `{content}`. This will break its intended use as a template.')
            exit(1)

        # Load all filenames in the markdown folder
        # This data is used to check which links are local
        files = {}
        for path in paths['md_folder'].rglob('*'):
            if path.is_dir():
                continue
            rel_path_posix = path.relative_to(paths['md_folder']).as_posix()
            files[rel_path_posix] = {'fullpath': str(path.resolve()), 'processed': False}  

        pb.files = files
        pb.html_template = html_template
        pb.dynamic_inclusions = dynamic_inclusions

        # Start conversion from the entrypoint
        ConvertMarkdownPageToHtmlPage(str(paths['md_entrypoint']), pb)

        # Keep going until all other files are processed
        if pb.gc('toggles','process_all') == True:
            print('\t> FEATURE: PROCESS ALL')
            unparsed = {}
            for k in files.keys():
                if files[k]["processed"] == False:
                    unparsed[k] = files[k]

            i = 0
            l = len(unparsed.keys())
            for k in unparsed.keys():
                i += 1
                if pb.gc('toggles','verbose_printout') == True:
                    print(f'\t\t{i}/{l} - ' + unparsed[k]['fullpath'])
                ConvertMarkdownPageToHtmlPage(unparsed[k]['fullpath'], pb, log_level=2)
            print('\t< FEATURE: PROCESS ALL: Done')

        # [18] Add in backlinks
        # ------------------------------------------
        if pb.gc('toggles','features','backlinks','enabled'):
            # Make lookup so that we can easily find the url of a node
            pb.network_tree.compile_node_lookup()

            # for each file in output
            for path in paths['html_output_folder'].rglob('*'):
                if path.is_dir():
                    continue

                # not all files are utf-8 readable, just ignore those
                try:
                    with open(path, 'r', encoding="utf-8") as f:
                        html = f.read()
                except:
                    continue
                
                # Get node_id
                m = re.search(r'(?<=\{_obsidian_html_backlinks_pattern_:)(.*?)(?=\})', html)
                if m is None:
                    continue
                node_id = m.group(0)

                # Compile backlinks list
                snippet = '<h2>Backlinks</h2>'
                snippet += '\n<ul>\n'
                i = 0
                for l in pb.network_tree.tree['links']:
                    if l['target'] == node_id:
                        url = pb.network_tree.node_lookup[l["source"]]['url']
                        snippet += f'\t<li><a class="backlink" href="{url}">{l["source"]}</a></li>\n'
                        i += 1
                snippet += '</ul>'

                # remove everything if no backlinks are present
                # (otherwise we have a header with no content below it)
                if i == 0:
                    snippet = ''

                # replace placeholder with list
                html = re.sub('\{_obsidian_html_backlinks_pattern_:'+re.escape(node_id)+'}', snippet, html)

                with open(path, 'w', encoding="utf-8") as f:
                    f.write(html)

        # Create tag page
        recurseTagList(pb.tagtree, '', pb, level=0)

        # Add Extra stuff to the output directories
        ExportStaticFiles(pb, pb.gc('toggles','features','graph','enabled'), pb.gc('html_url_prefix'), pb.gc('site_name'))

        # Write node json to static folder
        with open (pb.paths['html_output_folder'].joinpath('obs.html').joinpath('data/graph.json'), 'w', encoding="utf-8") as f:
            f.write(pb.network_tree.OutputJson())

    print('< COMPILING HTML FROM MARKDOWN CODE: Done')

    if pb.gc('toggles','features','rss','enabled'):
        print('> COMPILING RSS FEED')
        feed = RssFeed(pb)
        feed.Compile()
        print('< COMPILING RSS FEED: Done')

    if pb.gc('toggles','features','create_index_from_dir_structure','enabled'):
        rel_output_path = pb.gc('toggles','features','create_index_from_dir_structure','rel_output_path')
        op = paths['html_output_folder'].joinpath(rel_output_path)

        print(f'> COMPILING INDEX FROM DIR STRUCTURE ({op})')
        treeobj = CreateIndexFromDirStructure(pb, pb.paths['html_output_folder'])
        treeobj.BuildIndex()
        treeobj.WriteIndex()
        print('< COMPILING INDEX FROM DIR STRUCTURE: Done')


