import sys                  # commandline arguments
import os                   #
import shutil               # used to remove a non-empty directory, copy files
import uuid
import re                   # regex string finding/replacing
from pathlib import Path    # 
import markdown             # convert markdown to html
import yaml
import urllib.parse         # convert link characters like %
import frontmatter
import json
import warnings

from .MarkdownPage import MarkdownPage
from .MarkdownLink import MarkdownLink
from .lib import    DuplicateFileNameInRoot, \
                    GetObsidianFilePath, OpenIncludedFile, ExportStaticFiles, \
                    IsValidLocalMarkdownLink, PopulateTemplate, \
                    image_suffixes
from .PicknickBasket import PicknickBasket

# Open source files in the package
import importlib.resources as pkg_resources
import importlib.util
from . import src 

def recurseObisidianToMarkdown(page_path_str, pb):
    '''This functions converts an obsidian note to a markdown file and calls itself on any local note links it finds in the page.'''

    # Unpack picknick basket so we don't have to type too much.
    paths = pb.paths        # Paths of interest, such as the output and input folders
    files = pb.files        # Hashtable of all files found in the obsidian vault
    config = pb.config

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
    md.ConvertObsidianPageToMarkdownPage(paths['md_folder'], paths['obsidian_entrypoint'])

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
            continue
        link_path = link[0]

        # Mark the file as processed so that it will not be processed again at a later stage
        files[link_path]['processed'] = True         

        # Convert the note that is linked to
        if config['toggles']['verbose_printout']:
            print(f"converting {files[link_path]['fullpath']} (parent {page_path})")

        recurseObisidianToMarkdown(files[link_path]['fullpath'], pb)

def ConvertMarkdownPageToHtmlPage(page_path_str, pb, backlinkNode=None):
    '''This functions converts a markdown page to an html file and calls itself on any local markdown links it finds in the page.'''
    
    # Unpack picknick basket so we don't have to type too much.
    paths = pb.paths                    # Paths of interest, such as the output and input folders
    files = pb.files                    # Hashtable of all files found in the obsidian vault
    html_template = pb.html_template    # Built-in or user-provided html template
    config = pb.config

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
    
    # Use filename as node id, unless 'graph_name' is set in the yaml frontmatter
    node['id'] = str(md.rel_dst_path).split('/')[-1].replace('.md', '')
    if 'graph_name' in md.metadata.keys():
        node['id'] = md.metadata['graph_name']

    # Url is used so you can open the note/node by clicking on it
    node['url'] = f'{config["html_url_prefix"]}/{str(md.rel_dst_path)[:-3]}.html'
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

    if config['toggles']['verbose_printout']:
        print("html: converting ", page_path.as_posix(), " (parent ", md.src_path, ")")

    # [1] Replace code blocks with placeholders so they aren't altered
    # They will be restored at the end
    # ------------------------------------------------------------------
    md.StripCodeSections()     

    # Get all local markdown links. 
    # ------------------------------------------------------------------
    # This is any string in between '](' and  ')'
    proper_links = re.findall("(?<=\]\().+?(?=\))", md.page)
    for l in proper_links:
        # Init link
        link = MarkdownLink(l, page_path, paths['md_folder'], url_unquote=True, relative_path_md = config['toggles']['relative_path_md'])

        # Don't process in the following cases
        if link.isValid == False or link.isExternal == True: 
            continue

        # [12] Copy non md files over wholesale, then we're done for that kind of file
        if link.suffix != '.md' and link.suffix not in image_suffixes:
            paths['html_output_folder'].joinpath(link.rel_src_path).parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copyfile(link.src_path, paths['html_output_folder'].joinpath(link.rel_src_path))
            except FileNotFoundError:
                print('File ' + str(link.src_path) + ' not located, so not copied.')
            continue

        # [13] Link to a custom 404 page when linked to a not-created note
        if link.url.split('/')[-1] == 'not_created.md':
            new_link = f']({config["html_url_prefix"]}/not_created.html)'
        else:
            if link.rel_src_path_posix not in files.keys():
                continue

            md.links.append(link.rel_src_path_posix)

            # [11.1] Rewrite .md links to .html (when the link is to a file in our root folder)
            query_part = ''
            if link.query != '':
                query_part = link.query_delimiter + link.query 
            new_link = f']({config["html_url_prefix"]}/{link.rel_src_path_posix[:-3]}.html{query_part})'
            
        # Update link
        safe_link = re.escape(']('+l+')')
        md.page = re.sub(safe_link, new_link, md.page)

    # [4] Handle local image links (copy them over to output)
    # ------------------------------------------------------------------
    for link in re.findall("\!\[.*\]\((.*?)\)", md.page):
        l = urllib.parse.unquote(link)
        full_link_path = page_path.parent.joinpath(l).resolve()
        rel_path = full_link_path.relative_to(paths['md_folder'])

        # Only handle local image files (images located in the root folder)
        # Doublecheck, who knows what some weird '../../folder/..' does...
        if rel_path.as_posix() not in files.keys():
            if config['toggles']['warn_on_skipped_image']:
                warnings.warn(f"Image {str(full_link_path)} treated as external and not imported in html")
            continue

        # Copy src to dst
        dst_path = paths['html_output_folder'].joinpath(rel_path)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(full_link_path, dst_path)

        # [11.2] Adjust image link in page to new dst folder (when the link is to a file in our root folder)
        new_link = '![]('+urllib.parse.quote(config['html_url_prefix']+'/'+rel_path.as_posix())+')'
        safe_link = "\!\[.*\]\("+re.escape(link)+"\)"
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
    html_body = markdown.markdown(md.page, extensions=['extra', 'codehilite', 'toc', 'md_mermaid'], extension_configs=extension_configs)

    # HTML Tweaks
    # ------------------------------------------------------------------
    # [14] Tag external links with a class so they can be decorated differently
    for l in re.findall(r'(?<=\<a href=")([^"]*)', html_body):
        if l == '':
            continue
        if l[0] == '/':
            # Internal link, skip
            continue

        new_str = f"<a href=\"{l}\" class=\"external-link\""
        safe_str = f"<a href=\"{l}\""
        html_body = html_body.replace(safe_str, new_str)

    # [15] Tag not created links with a class so they can be decorated differently
    html_body = html_body.replace(f'<a href="{config["html_url_prefix"]}/not_created.html">', f'<a href="{config["html_url_prefix"]}/not_created.html" class="nonexistent-link">')

    # [17] Add in graph code to template (via {content})
    # This shows the "Show Graph" button, and adds the js code to handle showing the graph
    if config['toggles']['features']['graph']['enabled']:
        graph_template = OpenIncludedFile('graph_template.html')
        graph_template = graph_template.replace('{id}', simpleHash(html_body))\
                                       .replace('{pinnedNode}', node['id'])\
                                       .replace('{html_url_prefix}', config['html_url_prefix'])\
                                       .replace('{graph_coalesce_force}', config['toggles']['features']['graph']['coalesce_force'])
        html_body += f"\n{graph_template}\n"

    # [16] Wrap body html in valid html structure from template
    # ------------------------------------------------------------------
    html = PopulateTemplate(pb, html_template, content=html_body)

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
        if config['toggles']['verbose_printout']:
            print("html: initiating conversion for ", files[link_path]['fullpath'], " (parent ", md.src_path, ")")

        ConvertMarkdownPageToHtmlPage(files[link_path]['fullpath'], pb, backlinkNode)

def recurseTagList(tagtree, tagpath, pb, level):
    '''This function creates the folder `tags` in the html_output_folder, and a filestructure in that so you can navigate the tags.'''

    # Get relevant paths
    # ---------------------------------------------------------
    html_url_prefix = pb.config['html_url_prefix']
    tag_dst_path = pb.paths['html_output_folder'].joinpath(f'{tagpath}index.html').resolve()
    tag_dst_path_posix = tag_dst_path.as_posix()
    rel_dst_path_as_posix = tag_dst_path.relative_to(pb.paths['html_output_folder']).as_posix()

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
    html_body = markdown.markdown(md, extensions=['extra', 'codehilite', 'toc', 'md_mermaid'])

    di = '<link rel="stylesheet" href="'+pb.config['html_url_prefix']+'/98682199-5ac9-448c-afc8-23ab7359a91b-static/taglist.css" />'
    html = PopulateTemplate(pb, pb.html_template, content=html_body, dynamic_includes=di)

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

def printHelpAndExit(exitCode:int):
    print('[Obsidian-html]')
    print('- Add -i </path/to/input.yml> to provide config')
    print('- Add -v for verbose output')
    print('- Add -h to get helptext')
    print('- Add -eht <target/path/file.name> to export the html template.')
    exit(exitCode)

def main():
    # Show help text
    # ---------------------------------------------------------
    if '-h' in sys.argv:
        printHelpAndExit(0)

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
            html = OpenIncludedFile('template.html')
            with open (export_html_template_target_path, 'w', encoding="utf-8") as t:
                t.write(html)
            print(f"Exported html template to {str(export_html_template_target_path)}.")
            exit(0)

    # Load input yaml
    # ---------------------------------------------------------
    input_yml_path_str = 'config.yml'
    for i, v in enumerate(sys.argv):
        if v == '-i':
            input_yml_path_str = sys.argv[i+1]
            break

    try:
        with open(input_yml_path_str, 'rb') as f:
            config = yaml.load(f.read(), Loader=yaml.SafeLoader)
    except FileNotFoundError:
        print(f'Could not locate the config file {input_yml_path_str}.\n  Please try passing the exact location of it with the `obsidianhtml -i /your/path/to/{input_yml_path_str}` parameter.')
        printHelpAndExit(1)

    # Overwrite conf
    for i, v in enumerate(sys.argv):
        if v == '-v':
            config['toggles']['verbose_printout'] = True

    # Set defaults
    set_graph_defaults = False 
    set_create_index_from_tags_defaults = False 

    if 'features' not in config['toggles']:
        config['toggles']['features'] = {}
        set_graph_defaults = True
        set_create_index_from_tags_defaults = True
    else:
        if 'graph' not in config['toggles']['features']:
            set_graph_defaults = True
        if 'create_index_from_tags' not in config['toggles']['features']:
            set_create_index_from_tags_defaults = True       

    if 'process_all' not in config['toggles']:
        config['toggles']['process_all'] = False

    if set_graph_defaults:
        config['toggles']['features']['graph'] = {}
        config['toggles']['features']['graph']['enabled'] = True
        config['toggles']['features']['graph']['coalesce_force'] = "-200"

    if set_create_index_from_tags_defaults:
        config['toggles']['features']['create_index_from_tags'] = {}
        config['toggles']['features']['create_index_from_tags']['enabled'] = False
        config['toggles']['features']['create_index_from_tags']['tags'] = []
        config['toggles']['features']['create_index_from_tags']['add_links_in_graph_tree'] = True

    # Set Paths
    # ---------------------------------------------------------
    paths = {
        'obsidian_folder': Path(config['obsidian_folder_path_str']).resolve(),
        'md_folder': Path(config['md_folder_path_str']).resolve(),
        'obsidian_entrypoint': Path(config['obsidian_entrypoint_path_str']).resolve(),
        'md_entrypoint': Path(config['md_entrypoint_path_str']).resolve(),
        'html_output_folder': Path(config['html_output_folder_path_str']).resolve()
    }

    # Deduce relative paths
    paths['rel_obsidian_entrypoint'] = paths['obsidian_entrypoint'].relative_to(paths['obsidian_folder'])
    paths['rel_md_entrypoint_path']  = paths['md_entrypoint'].relative_to(paths['md_folder'])


    # Compile dynamic inclusion list
    # ---------------------------------------------------------
    # This is a set of javascript/css files to be loaded into the header based on config choices.
    dynamic_inclusions = ""
    if config['toggles']['features']['graph']['enabled']:
        dynamic_inclusions += '<link rel="stylesheet" href="'+config["html_url_prefix"]+'/98682199-5ac9-448c-afc8-23ab7359a91b-static/graph.css" />' + "\n"
        dynamic_inclusions += '<script src="https://d3js.org/d3.v4.min.js"></script>' + "\n"


    # Remove previous output
    # ---------------------------------------------------------
    if config['toggles']['no_clean'] == False:
        print('> CLEARING OUTPUT FOLDERS')
        if config['toggles']['compile_md']:
            if paths['md_folder'].exists():
                shutil.rmtree(paths['md_folder'])

        if paths['html_output_folder'].exists():
            shutil.rmtree(paths['html_output_folder'])    

    # Recreate folder tree
    # ---------------------------------------------------------
    print('> CREATING OUTPUT FOLDERS')
    paths['md_folder'].mkdir(parents=True, exist_ok=True)
    paths['html_output_folder'].mkdir(parents=True, exist_ok=True)

    # Make "global" object that we can pass to functions
    # ---------------------------------------------------------
    pb = PicknickBasket(config, paths)

    # Convert Obsidian to markdown
    # ---------------------------------------------------------
    if config['toggles']['compile_md']:

        # Load all filenames in the root folder.
        # This data will be used to check which files are local, and to get their full path
        # It's clear that no two files can be allowed to have the same file name.
        files = {}
        for path in paths['obsidian_folder'].rglob('*'):
            if path.is_dir():
                continue

            # Exclude configured subfolders
            if 'exclude_subfolders' in config:
                _continue = False
                for folder in config['exclude_subfolders']:
                    excl_folder_path = paths['obsidian_folder'].joinpath(folder)
                    if path.resolve().is_relative_to(excl_folder_path):
                        if config['toggles']['verbose_printout']:
                            print(f'Excluded folder {excl_folder_path}: Excluded file {path.name}.')
                        _continue = True
                    continue
                if _continue:
                    continue

            # Check if filename is duplicate
            if path.name in files.keys() and config['toggles']['allow_duplicate_filenames_in_root'] == False:
                print(path)
                raise DuplicateFileNameInRoot(f"Two or more files with the name \"{path.name}\" exist in the root folder. See {str(path)} and {files[path.name]['fullpath']}.")

            # Add to tree
            files[path.name] = {'fullpath': str(path), 'processed': False}  

        pb.files = files

        # Create index.md based on given tagname, that will serve as the entrypoint
        # ---------------------------------------------------------
        if config['toggles']['features']['create_index_from_tags']['enabled']:
            if config['toggles']['verbose_printout']:
                print('> FEATURE: CREATE INDEX FROM TAGS: Enabled')

            # Test input
            if not isinstance(config['toggles']['features']['create_index_from_tags']['tags'], list):
                raise Exception("toggles/features/create_index_from_tags/tags should be a list")

            if len(config['toggles']['features']['create_index_from_tags']['tags']) == 0:
                raise Exception("Feature create_index_from_tags is enabled, but no tags were listed")

            # shorthand 
            include_tags = config['toggles']['features']['create_index_from_tags']['tags']
            if config['toggles']['verbose_printout']:
                print('Looking for tags: ', include_tags)

            # overwrite defaults
            index_dst_path = paths['md_folder'].joinpath('__tags_index.md').resolve()

            if config['toggles']['verbose_printout']:
                print('Will write the note index to: ', index_dst_path)
                print('Will overwrite entrypoints: md_entrypoint_path_str, obsidian_entrypoint, md_entrypoint, rel_md_entrypoint_path')

            config['md_entrypoint_path_str']       = str(index_dst_path)                              # should not be used anymore at this point, but just to be sure
            paths['obsidian_entrypoint']         = paths['obsidian_folder'].joinpath('dontparse')   # Set to nonexistent file without .md so the entrypoint becomes invalid
            paths['md_entrypoint']               = index_dst_path
            paths['rel_md_entrypoint_path']      = paths['md_entrypoint'].relative_to(paths['md_folder'])
            pb.paths = paths

            # Find notes with given tags
            _files = {}
            index_dict = {}
            for t in include_tags:
                index_dict[t] = []

            for k in files.keys():
                # Determine src file path
                page_path_str = files[k]['fullpath']
                page_path = Path(page_path_str).resolve()

                # Skip if not valid
                if not IsValidLocalMarkdownLink(page_path_str):
                    continue

                # Try to open file
                with open(page_path, encoding="utf-8") as f:
                    # Get frontmatter yaml
                    metadata, page = frontmatter.parse(f.read())

                    # Bug out if frontdata not present
                    if not isinstance(metadata, dict):
                        continue
                    if 'tags' not in metadata.keys():
                        continue

                    # get graphname of the page, we need this later
                    graph_name = k[:-3]
                    if 'graph_name' in metadata.keys():
                        graph_name = metadata['graph_name']


                    # Check for each of the tags if its present                    
                    for t in include_tags:
                        if t in metadata['tags']:
                            if config['toggles']['verbose_printout']:
                                print(f'Matched note {k} on tag {t}')

                            # copy file to temp filetree for checking later
                            _files[k] = files[k].copy()

                            # Add entry to our index dict so we can parse this later
                            md = MarkdownPage(page_path, paths['obsidian_folder'], files)
                            md.SetDestinationPath(paths['html_output_folder'], paths['md_entrypoint'])
                            index_dict[t].append((k, md.rel_dst_path.as_posix(), graph_name))

            if len(_files.keys()) == 0:
                raise Exception(f"No notes found with the given tags.")

            if not config['toggles']['process_all']:
                # Overwrite the filetree 
                files = _files

            if config['toggles']['verbose_printout']:
                print(f'Building index.md')

            index_md_content = f'# {config["site_name"]}\n'
            for t in index_dict.keys():
                # Add header
                index_md_content += f'## {t}\n'

                # Add notes as list
                for n in index_dict[t]:
                    index_md_content += f'- [{n[0][:-3]}]({n[1]})\n'
                index_md_content += '\n'

            # write content to markdown file
            with open(index_dst_path, 'w', encoding="utf-8") as f:
                f.write(index_md_content)

            # [17] Build graph node/links
            if config['toggles']['features']['create_index_from_tags']['add_links_in_graph_tree']:

                if config['toggles']['verbose_printout']:
                    print(f'Adding graph links between index.md and the matched notes')
                
                node = pb.network_tree.NewNode()
                node['id'] = 'index'
                node['url'] = f'{config["html_url_prefix"]}/index.html'
                pb.network_tree.AddNode(node)
                bln = node
                for t in index_dict.keys():
                    for n in index_dict[t]:
                        node = pb.network_tree.NewNode()
                        node['id'] = n[2]
                        node['url'] = f'{config["html_url_prefix"]}/{n[1][:-3]}.html'
                        pb.network_tree.AddNode(node)

                        link = pb.network_tree.NewLink()
                        link['source'] = bln['id']
                        link['target'] = node['id']
                        pb.network_tree.AddLink(link)

            if config['toggles']['verbose_printout']:
                print('< FEATURE: CREATE INDEX FROM TAGS: Done')


        # Start conversion with entrypoint.
        # ---------------------------------------------------------
        # Note: this will mean that any note not (indirectly) linked by the entrypoint will not be included in the output!
        print(f'> COMPILING MARKDOWN FROM OBSIDIAN CODE ({str(paths["obsidian_entrypoint"])})')
        recurseObisidianToMarkdown(str(paths['obsidian_entrypoint']), pb)

        # Keep going until all other files are processed
        if config['toggles']['process_all'] or config['toggles']['features']['create_index_from_tags']['enabled']:
            # Note: for case create_index_from_tags/enabled = True and process_all = False, 
            #       the files dict has been overwritten from including all files, to only the files matched on the provided tags 
            unparsed = {}
            for k in files.keys():
                if files[k]["processed"] == False:
                    unparsed[k] = files[k]

            i = 0
            l = len(unparsed.keys())
            for k in unparsed.keys():
                i += 1
                if config['toggles']['verbose_printout'] == True:
                    print(f'{i}/{l} - ' + unparsed[k]['fullpath'])
                recurseObisidianToMarkdown(unparsed[k]['fullpath'], pb)


    # Convert Markdown to Html
    # ------------------------------------------
    if config['toggles']['compile_html']:
        print(f'> COMPILING HTML FROM MARKDOWN CODE ({str(paths["md_entrypoint"])})')

        # Get html template code. 
        # Every note will become a html page, where the body comes from the note's markdown, 
        # and the wrapper code from this template.
        if  'html_template_path_str' in config.keys() and config['html_template_path_str'] != '':
            print('-------------')
            with open(Path(config['html_template_path_str']).resolve()) as f:
                html_template = f.read()
        else:
            html_template = OpenIncludedFile('template.html')

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
        if config['toggles']['process_all'] == True:
            unparsed = {}
            for k in files.keys():
                if files[k]["processed"] == False:
                    unparsed[k] = files[k]

            i = 0
            l = len(unparsed.keys())
            for k in unparsed.keys():
                i += 1
                if config['toggles']['verbose_printout'] == True:
                    print(f'{i}/{l} - ' + unparsed[k]['fullpath'])
                ConvertMarkdownPageToHtmlPage(unparsed[k]['fullpath'], pb)

        # Create tag page
        recurseTagList(pb.tagtree, 'tags/', pb, level=0)

        # Add Extra stuff to the output directories
        ExportStaticFiles(pb)

        # Write node json to static folder
        with open (pb.paths['html_output_folder'].joinpath('98682199-5ac9-448c-afc8-23ab7359a91b-static').joinpath('graph.json'), 'w', encoding="utf-8") as f:
            f.write(pb.network_tree.OutputJson())

        

    print('> DONE')
