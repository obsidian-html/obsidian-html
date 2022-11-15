
import sys
import markdown             # convert markdown to html
import frontmatter
import gzip
import shutil
import warnings
import yaml

import regex as re          # regex string finding/replacing

import urllib.parse         # convert link characters like %

from pathlib import Path    # 

from .PathFinder import OH_File, get_rel_html_url_prefix, get_html_url_prefix
from .FileFinder import GetNodeId, FindFile

from .MarkdownPage import MarkdownPage, ConvertMarkdownToHeaderTree
from .MarkdownLink import MarkdownLink
from .lib import    DuplicateFileNameInRoot, CreateTemporaryCopy, \
                    GetObsidianFilePath, OpenIncludedFile, ExportStaticFiles, CreateStaticFilesFolders, \
                    PopulateTemplate, WriteFileLog, simpleHash, get_default_appdir_config_yaml_path
from .RssFeed import RssFeed
from .ErrorHandling import extra_info
from .PicknickBasket import PicknickBasket
from .CreateIndexFromTags import CreateIndexFromTags
from .EmbeddedSearch import EmbeddedSearch, ConvertObsidianQueryToWhooshQuery
from .FileTree import FileTree

from .markdown_extensions.CallOutExtension import CallOutExtension
from .markdown_extensions.DataviewExtension import DataviewExtension
from .markdown_extensions.MermaidExtension import MermaidExtension
from .markdown_extensions.CustomTocExtension import CustomTocExtension
from .markdown_extensions.EraserExtension import EraserExtension
from .markdown_extensions.FootnoteExtension import FootnoteExtension
from .markdown_extensions.FormattingExtension import FormattingExtension
from .markdown_extensions.EmbeddedSearchExtension import EmbeddedSearchExtension
from .markdown_extensions.CodeWrapperExtension import CodeWrapperExtension
from .markdown_extensions.AdmonitionExtension import AdmonitionExtension
#from .markdown_extensions.CustomTableExtension import CustomTableExtension

def ConvertVault(config_yaml_location=''):
    # Make "global" object that we can pass to functions
    # ---------------------------------------------------------
    pb = PicknickBasket()

    # Other commandline arguments
    # ---------------------------------------------------------
    # Set verbosity (overwrite config)
    for i, v in enumerate(sys.argv):
        if v == '-v':
            pb.verbose = True
            break

    # Set config
    if config_yaml_location != '':
        input_yml_path_str = config_yaml_location
    else:
        input_yml_path_str = ''
        for i, v in enumerate(sys.argv):
            if v == '-i':
                if len(sys.argv) < (i + 2):
                    print(f'No config path given.\n  Use `obsidianhtml convert -i /target/path/to/config.yml` to provide input.')
                    #print_global_help_and_exit(1)
                    exit(1)
                input_yml_path_str = sys.argv[i+1]
                break

    # Try to find config in default locations
    if input_yml_path_str == '':
        # config.yml in same folder
        if Path('config.yml').exists():
            input_yml_path_str = Path('config.yml').resolve().as_posix()
            print(f"No config provided, using config at {input_yml_path_str} (Default config path)")
    if input_yml_path_str == '':
        # config.yaml in same folder
        if Path('config.yaml').exists():
            input_yml_path_str = Path('config.yaml').resolve().as_posix()
            print(f"No config provided, using config at {input_yml_path_str} (Default config path)")
    if input_yml_path_str == '':
        # config.yml in appdir folder
        appdir_config = Path(get_default_appdir_config_yaml_path())
        if appdir_config.exists():
            input_yml_path_str = appdir_config.as_posix()
            print(f"No config provided, using config at {input_yml_path_str} (Default config path)")

    if input_yml_path_str == '':
        print(f'No config path given, and none found in default locations.\n  Use `obsidianhtml convert -i /target/path/to/config.yml` to provide input.')
        exit(1)

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
    paths['dataview_export_folder'] = paths['obsidian_folder'].joinpath(pb.gc('toggles/features/dataview/folder'))

    if pb.gc('toggles/extended_logging', cached=True):
        paths['log_output_folder'] = Path(pb.gc('log_output_folder_path_str')).resolve()

    # Deduce relative paths
    if pb.gc('toggles/compile_md', cached=True):
        paths['rel_obsidian_entrypoint'] = paths['obsidian_entrypoint'].relative_to(paths['obsidian_folder'])
    paths['rel_md_entrypoint_path']  = paths['md_entrypoint'].relative_to(paths['md_folder'])
    
    # Add paths to pb
    # ---------------------------------------------------------
    pb.paths = paths

    # Copy vault to tempdir, so any bugs will not affect the user's vault
    # ---------------------------------------------------------
    if pb.gc('copy_vault_to_tempdir') and pb.gc('toggles/compile_md'):
        # Copy over vault to tempdir
        tmpdir = CreateTemporaryCopy(source_folder_path=pb.paths['obsidian_folder'], pb=pb)

        # update paths
        pb.paths['original_obsidian_folder'] = pb.paths['obsidian_folder']        # use only for lookups!
        pb.paths['obsidian_folder'] = Path(tmpdir.name).resolve()
        pb.paths['obsidian_entrypoint'] = pb.paths['obsidian_folder'].joinpath(pb.paths['rel_obsidian_entrypoint'])
    else:
        pb.paths['original_obsidian_folder'] = pb.paths['obsidian_folder']        # use only for lookups!

    # Compile dynamic inclusion list
    # ---------------------------------------------------------
    # This is a set of javascript/css files to be loaded into the header based on config choices.
    dynamic_inclusions = ""
    try:
        dynamic_inclusions += '\n'.join(pb.gc('html_custom_inclusions')) +'\n'
    except:
        None
    pb.dynamic_inclusions = dynamic_inclusions

    # This is a set of javascript/css files to be loaded into the footer based on config choices.
    dynamic_footer_inclusions = ""
    try:
        dynamic_footer_inclusions += '\n'.join(pb.gc('html_custom_footer_inclusions')) +'\n'
    except:
        None
    pb.dynamic_footer_inclusions = dynamic_footer_inclusions


    # Remove potential previous output
    # ---------------------------------------------------------
    if pb.gc('toggles/no_clean', cached=True) == False:
        print('> CLEARING OUTPUT FOLDERS')
        if pb.gc('toggles/compile_md', cached=True):
            if pb.paths['md_folder'].exists():
                shutil.rmtree(pb.paths['md_folder'])

        if pb.paths['html_output_folder'].exists():
            shutil.rmtree(pb.paths['html_output_folder'])    

    # Create folder tree
    # ---------------------------------------------------------
    print('> CREATING OUTPUT FOLDERS')

    if pb.gc('toggles/compile_md', cached=True):
        pb.paths['md_folder'].mkdir(parents=True, exist_ok=True)

    pb.paths['html_output_folder'].mkdir(parents=True, exist_ok=True)
    pb.paths['html_output_folder'] = pb.paths['html_output_folder'].resolve()
    
    if pb.gc('toggles/extended_logging', cached=True):
        pb.paths['log_output_folder'].mkdir(parents=True, exist_ok=True)
        pb.paths['log_output_folder'] = pb.paths['log_output_folder'].resolve()


    ft = FileTree(pb)
    ft.load_file_tree()
    #print(yaml.dump([x for x in pb.files.keys()]))


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
        print(f'> COMPILING MARKDOWN FROM OBSIDIAN CODE ({str(pb.paths["obsidian_entrypoint"])})')

        if pb.gc('toggles/debug_filetree_keys'):
            for k, v in pb.files.items():
                print(k)

        # Force search to lowercase
        rel_entry_path_str = pb.paths['rel_obsidian_entrypoint'].as_posix()
        if pb.gc('toggles/force_filename_to_lowercase', cached=True):
            rel_entry_path_str = rel_entry_path_str.lower()

        # Start conversion
        ep = pb.files[rel_entry_path_str]
        pb.init_state(action='n2m', loop_type='note', current_fo=ep, subroutine='recurseObisidianToMarkdown')
        recurseObisidianToMarkdown(ep, pb)
        pb.reset_state()

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
                pb.init_state(action='n2m_process_all', loop_type='note', current_fo=fo, subroutine='recurseObisidianToMarkdown')
                recurseObisidianToMarkdown(fo, pb, log_level=2)
                pb.reset_state()
            print('\t< FEATURE: PROCESS ALL: Done')

    if pb.gc('toggles/extended_logging', cached=True):
        WriteFileLog(pb.files, pb.paths['log_output_folder'].joinpath('files_ntm.md'), include_processed=True)


    # Convert Markdown to Html
    # ------------------------------------------
    if pb.gc('toggles/compile_html', cached=True):
        print(f'> COMPILING HTML FROM MARKDOWN CODE ({str(pb.paths["md_entrypoint"])})')

        html_url_prefix = pb.gc("html_url_prefix")

        # compile navbarlinks
        navbar_links = pb.gc('navbar_links', cached=True)
        elements = []
        for l in navbar_links:
            # default
            el = f'<a class="navbar-link" href="{html_url_prefix}/{l["link"]}" title="{l["name"]}">{l["name"]}</a>'

            # external links
            if 'type' in l.keys():
                if l['type'] == 'external':
                    el = f'<a class="navbar-link" href="{l["link"]}" title="{l["name"]}">{l["name"]}</a>'
                else:
                    raise Exception(f"navbar_link type of {l['type']} is unknown. Known types: external (for internal links just remove the type keyvalue pair)")

            elements.append(el)

        pb.navbar_links = elements

        # [??] Embedded note titles integration
        # ------------------------------------------------------------------
        if pb.gc('toggles/features/embedded_note_titles/enabled', cached=True):
            if pb.gc('toggles/verbose_printout', cached=True):
                print('\t'*(1), f"html: embedded note titles are enabled in config")

            # Enable/disable capability based on whether the plugin is installed
            embed_plugin_folder_path = pb.paths['original_obsidian_folder'].joinpath('.obsidian/plugins/obsidian-embedded-note-titles').resolve()
            pb.config.capabilities_needed['embedded_note_titles'] = embed_plugin_folder_path.exists()
            if pb.gc('toggles/verbose_printout', cached=True):
                if pb.config.capabilities_needed['embedded_note_titles']:
                    print('\t'*(1), f"html: embedded note title plugin found, enabling embedded_note_titles capability.")
                else:
                    print('\t'*(1), f"html: embedded note title plugin not found, disabling embedded_note_titles capability.")

            # Load config
            if pb.config.capabilities_needed['embedded_note_titles']:
                data_path = embed_plugin_folder_path.joinpath('data.json').resolve()
                result = pb.config.LoadEmbeddedNoteConfig(data_path)

                if pb.gc('toggles/verbose_printout', cached=True):
                    if result:
                        print('\t'*(1), f"html: embedded note titles settings loaded.", pb.config.plugin_settings['embedded_note_titles'])
                    else:
                        print('\t'*(1), f"html: embedded note titles settings were not found, using defaults.")
        else:
            pb.config.capabilities_needed['embedded_note_titles'] = False
            if pb.gc('toggles/verbose_printout', cached=True):
                print('\t'*(1), f"html: embedded note titles are disabled in config")

        # Force search to lowercase
        rel_entry_path_str = paths['rel_md_entrypoint_path'].as_posix()
        if pb.gc('toggles/force_filename_to_lowercase', cached=True):
            rel_entry_path_str = rel_entry_path_str.lower()

        # Start conversion from the entrypoint
        ep = pb.files[rel_entry_path_str]
        pb.init_state(action='m2h', loop_type='md_note', current_fo=ep, subroutine='ConvertMarkdownPageToHtmlPage')
        ConvertMarkdownPageToHtmlPage(ep, pb)
        pb.reset_state()

        # Keep going until all other files are processed
        if pb.gc('toggles/process_all') == True:
            print('\t> FEATURE: PROCESS ALL')
            unparsed = [x for x in pb.files.values() if x.processed_mth == False]
            i = 0; l = len(unparsed)
            for fo in unparsed:
                i += 1
                if pb.gc('toggles/verbose_printout', cached=True) == True:
                    print(f'\t\t{i}/{l} - ' + str(fo.path['markdown']['file_absolute_path']))

                pb.init_state(action='m2h_process_all', loop_type='md_note', current_fo=fo, subroutine='ConvertMarkdownPageToHtmlPage')
                ConvertMarkdownPageToHtmlPage(fo, pb, log_level=2)
                pb.reset_state()

            print('\t< FEATURE: PROCESS ALL: Done')

        if pb.gc('toggles/extended_logging', cached=True):
            WriteFileLog(pb.files, pb.paths['log_output_folder'].joinpath('files_mth.md'), include_processed=True)

        # [??] Create html file tree
        # ------------------------------------------
        if pb.gc('toggles/features/create_index_from_dir_structure/enabled'):
            rel_output_path = pb.gc('toggles/features/create_index_from_dir_structure/rel_output_path')
            op = pb.paths['html_output_folder'].joinpath(rel_output_path)

            print(f'\t> COMPILING INDEX FROM DIR STRUCTURE ({op})')
            # Create dirtree to be viewed on its own
            if pb.gc('toggles/relative_path_html', cached=True):
                html_url_prefix = pb.sc(path='html_url_prefix', value=get_rel_html_url_prefix(pb.gc('toggles/features/create_index_from_dir_structure/rel_output_path')))
                print(html_url_prefix)
            pb.EnsureTreeObj()
            pb.treeobj.rel_output_path = pb.gc('toggles/features/create_index_from_dir_structure/rel_output_path')
            pb.treeobj.html_url_prefix = pb.gc('html_url_prefix')
            pb.treeobj.html = pb.treeobj.BuildIndex()
            pb.treeobj.WriteIndex()
            
            # Create dirtree to be included in every page
            if pb.gc('toggles/relative_path_html', cached=True):
                html_url_prefix = pb.sc(path='html_url_prefix', value='')
            pb.EnsureTreeObj()
            pb.treeobj.rel_output_path = 'obs.html/dirtree.html'
            pb.treeobj.html_url_prefix = pb.gc('html_url_prefix')
            pb.treeobj.html = pb.treeobj.BuildIndex()
            pb.treeobj.WriteIndex()


            print('\t< COMPILING INDEX FROM DIR STRUCTURE: Done')

        # [??] Second pass
        # ------------------------------------------
        # Some code can only be generated when all the notes have already been created.
        # These steps are done in this block.

        # Make lookup so that we can easily find the url of a node
        pb.network_tree.compile_node_lookup()

        # Get some data outside of the loop
        dir_repstring = '{left_pane_content}'
        dir_repstring2 = '{right_pane_content}'
        if pb.gc('toggles/features/styling/flip_panes', cached=True):
            dir_repstring = '{right_pane_content}'
            dir_repstring2 = '{left_pane_content}'

        esearch = None
        if pb.gc('toggles/features/embedded_search/enabled', cached=True):
            esearch = EmbeddedSearch(json_data=pb.search.OutputJson())
        
        print('\t> SECOND PASS HTML')

        for fo in pb.files.values():
            if not fo.metadata['is_note']:
                continue

            # get paths / html prefix
            dst_abs_path = fo.path['html']['file_absolute_path']
            dst_rel_path_str = fo.path['html']['file_relative_path'].as_posix()
            html_url_prefix = get_html_url_prefix(pb, rel_path_str=dst_rel_path_str)
            page_depth = len(dst_rel_path_str.split('/')) - 1

            # get html content
            try:
                with open(dst_abs_path, 'r', encoding="utf-8") as f:
                    html = f.read()
            except:
                continue

            # Get node_id
            m = re.search(r'(?<=\{_obsidian_html_node_id_pattern_:)(.*?)(?=\})', html)
            if m is None:
                continue
            node_id = m.group(0)
            node = pb.network_tree.node_lookup[node_id]

            html = re.sub('\{_obsidian_html_node_id_pattern_:'+node_id+'}', '', html)

            # Create Directory contents
            if pb.gc('toggles/features/styling/add_dir_list', cached=True):
                if dir_repstring in html:
                    pb.EnsureTreeObj()
                    dir_list = pb.treeobj.BuildIndex(current_page=node['url'])
                    html = re.sub(dir_repstring, dir_list, html)
                    html = re.sub(dir_repstring2, '', html)

            # Compile backlinks list
            if pb.gc('toggles/features/backlinks/enabled', cached=True):
                backlinks = [x for x in pb.network_tree.tree['links'] if x['target'] == node_id]
                snippet = ''
                if len(backlinks) > 0:
                    snippet = "<h2>Backlinks</h2>\n<ul>\n"
                    for l in backlinks:
                        if l['target'] == node_id:
                            url = pb.network_tree.node_lookup[l['source']]['url']
                            if pb.gc('toggles/relative_path_html', cached=True):
                                url = ('../' * page_depth) + pb.network_tree.node_lookup[l['source']]['rtr_url']
                            if url[0] not in ['.', '/']:
                                url = '/'+url
                            snippet += f'\t<li><a class="backlink" href="{url}">{l["source"]}</a></li>\n'
                    snippet += '</ul>'
                    snippet = f'<div class="backlinks">\n{snippet}\n</div>\n'
                else:
                    snippet = f'<div class="backlinks" style="display:none"></div>\n'

                # replace placeholder with list & write output
                html = re.sub('\{_obsidian_html_backlinks_pattern_\}', snippet, html)

            # Compile tags list
            if pb.gc('toggles/features/tags_page/styling/show_in_note_footer', cached=True):
                # Replace placeholder
                snippet = ''
                if 'tags' in node['metadata'] and len(node['metadata']['tags']) > 0:
                    snippet = "<h2>Tags</h2>\n<ul>\n"
                    for tag in node['metadata']['tags']:
                        url = f'{pb.gc("html_url_prefix")}/obs.html/tags/{tag}/index.html'
                        snippet += f'\t<li><a class="backlink" href="{url}">{tag}</a></li>\n'

                        if pb.gc('toggles/preserve_inline_tags', cached=True):
                            placeholder = re.escape("<code>{_obsidian_pattern_tag_" + tag + "}</code>")
                            inline_tag = f'<a class="inline-tag" href="{url}">{tag}</a>'
                            html = re.sub(placeholder, inline_tag, html)

                    snippet += '</ul>'

                # replace placeholder with list & write output
                html = re.sub('\{_obsidian_html_tags_footer_pattern_\}', snippet, html)


            # add breadcrumbs
            if pb.gc('toggles/features/breadcrumbs/enabled', cached=True):

                if node['url'] == '/index.html':
                    snippet = ''
                else:
                    html_url_prefix = pb.gc("html_url_prefix", cached=True)
                    parts = [f'<a href="{html_url_prefix}/" style="color: rgb(var(--normal-text-color));">Home</a>']

                    previous_url = ''
                    subpaths = node['url'].replace('.html', '').split('/')[1:]
                    match_subpaths = subpaths
                    
                    if pb.gc('toggles/force_filename_to_lowercase', cached=True):
                        match_subpaths = [ x.lower() for x in subpaths]

                    if html_url_prefix:
                        subpaths = subpaths[1:]
                        match_subpaths = match_subpaths[1:]

                    for i, msubpath in enumerate(match_subpaths):
                        if i == len(msubpath) - 1:
                            if node["url"] != previous_url:
                                parts.append(f'<a href="{node["url"]}" ___COLOR___ >{subpaths[i]}</a>')
                            continue
                        else:
                            if msubpath in pb.network_tree.node_lookup:
                                url = pb.network_tree.node_lookup[msubpath]['url']
                                if url != previous_url:
                                    parts.append(f'<a href="{url}" ___COLOR___>{subpaths[i]}</a>')
                                previous_url = url
                                continue
                            else:
                                parts.append(f'<span style="color: #666;">{subpaths[i]}</span>')
                                previous_url = ''
                                continue

                    parts[-1] = parts[-1].replace('___COLOR___', '')
                    for i, link in enumerate(parts):
                        parts[i] = link.replace('___COLOR___', 'style="color: var(--normal-text-color);"')
                            

                    snippet = ' / '.join(parts)
                    snippet = f'''
                    <div style="width:100%; text-align: right;display: block;margin: 0.5rem;">
                        <div style="flex:1;display: none;"></div>
                        <div class="breadcrumbs" style="flex:1 ;padding: 0.5rem; width: fit-content;display: inline;border-radius: 0.2rem;">
                            {snippet}
                        </div>
                    </div>'''

                html = re.sub('\{_obsidian_html_breadcrumbs_pattern_\}', snippet, html)

            # add embedded search results
            if pb.gc('toggles/features/embedded_search/enabled', cached=True):
                query_blocks = re.findall(r'(?<=<p>{_obsidian_html_query:)(.*?)(?=\ }</p>)', html)
                for listing in query_blocks:
                    # split listing into qualifier and user_query
                    qual, user_query = listing.split('|-|')

                    # found query
                    print(qual, user_query)

                    # search
                    res = esearch.search(user_query)

                    # compile html output
                    output = ''
                    if qual == 'list':
                        output = '<div class="query"><ul>\n\t' + '\n\t'.join([f'<li><a href="/{x["path"]}">{x["title"]}</a></li>' for x in res]) + '\n</ul></div>'
                    
                    else:
                        output = '<div class="query">'
                        for doc in res:
                            # setup doc
                            output += f'\n\t<div class="match-document">\n\t\t<div class="match-document-title">\n\t\t\t<a href="/{doc["path"]}">{doc["title"]}</a>\n\t\t</div>\n\t\t<div class="matches">'
                            
                            # Add path matches
                            if doc['matches']['path']:
                                output += f'\n\t\t\t<div class="match-row">\n\t\t\t\t' + doc['matches']['path'] + '\n\t\t\t</div>'

                            # Add content mathes
                            for match in doc['matches']['content']:
                                output += f'\n\t\t\t<div class="match-row">\n\t\t\t\t{match}\n\t\t\t</div>'

                            # Add tags
                            if len(doc['matches']['tags']) > 0:
                                output += '\n\t\t\t<div class="tag-box">'
                                for match, tag in doc['matches']['tags']:
                                    output += f'\n\t\t\t\t<div class="match-row tag">\n\t\t\t\t\t<a href="/obs.html/tags/{tag}/index.html">{match}</a>\n\t\t\t\t</div>'
                                output += '\n\t\t\t</div>'

                            if len(doc['matches']['tags_keyword']) > 0:
                                output += '\n\t\t\t<div class="tag-box">'
                                for match, tag in doc['matches']['tags_keyword']:
                                    output += f'\n\t\t\t\t<div class="match-row tag keyword">\n\t\t\t\t\t<a href="/obs.html/tags/{tag}/index.html">{match}</a>\n\t\t\t\t</div>'
                                output += '\n\t\t\t</div>'

                            # close doc divs
                            output += '\n\t\t</div>\n\t</div>'
                        # close query div
                        output += '\n</div>'

                    # replace query block with html
                    safe_str = re.escape('<p>{_obsidian_html_query:' + listing + ' }</p>')
                    html = re.sub(safe_str, output, html)

            # write result
            with open(dst_abs_path, 'w', encoding="utf-8") as f:
                f.write(html)
            
        print('\t< SECOND PASS HTML: Done')

        # Create tag page
        recurseTagList(pb.tagtree, '', pb, level=0)

        # Test: foldable tag list
        def rec_tag_tree_foldable(tag_tree, name, id, path=''):
            subid = 0

            notes = ''
            if tag_tree['notes']:
                notes += '<div class="tags-notes" style="font-weight:normal;"><ul class="tag-list">'
                tag_tree['notes'].sort()
                for note in tag_tree['notes']:
                    note_name = note.split('/')[-1].replace(".html", "")
                    ahref = f'<a href="{pb.gc("html_url_prefix")}/{note}">{note_name}</a>'
                    notes += f'<li>{ahref}</li>'
                notes += '</ul></div>'

            subtags = ''
            subtags_keys = list(tag_tree['subtags'].keys())
            subtags_keys.sort()
            for key in subtags_keys:
                subtags += rec_tag_tree_foldable(tag_tree['subtags'][key], key, str(id)+str(subid), '/'.join(list(filter(None, [path, name]))))
                subid += 1

            header = ''
            contents = f'{subtags}{notes}'
            if name:
                if path:
                    path += '/'
                header = f'<button class="dir-button" onclick="toggle_id(\'{id}\')"><span class="tag-path">{path} </span>{name.capitalize()}</button>'
                contents = f'<div class="dir-container" id="{id}" style="font-weight:normal;">{contents}</div>'

            html = f'<div class="subtags">{header}{contents}</div>'
            return html

        # set output path
        tags_folder = pb.paths['html_output_folder'].joinpath('obs.html/tags/')
        tag_dst_path = tags_folder.joinpath('index.html')
        tag_dst_path_posix = tag_dst_path.as_posix()
        tag_dst_path.parent.mkdir(parents=True, exist_ok=True)

        rel_dst_path_as_posix = tag_dst_path.relative_to(pb.paths['html_output_folder']).as_posix()

        # set html_url_prefix
        if pb.gc('toggles/relative_path_html', cached=True):
            html_url_prefix = pb.sc(path='html_url_prefix', value=get_rel_html_url_prefix(rel_dst_path_as_posix))

        # compile html
        html = rec_tag_tree_foldable(pb.tagtree, '', 'tags-')
        html = PopulateTemplate(pb, 'none', pb.dynamic_inclusions, pb.html_template, html_url_prefix=html_url_prefix, content=html, container_wrapper_class_list=['single_tab_page-left-aligned'])
        html = html.replace('{pinnedNode}', 'tagspage')
        html = html.replace('{{navbar_links}}', '\n'.join(pb.navbar_links)) 
        html = html.replace('{left_pane_content}', '')\
                .replace('{right_pane_content}', '')

        # write to destination
        with open(tag_dst_path_posix, 'w', encoding="utf-8") as f:
            f.write(html) 


        # Create graph fullpage
        if pb.gc('toggles/features/graph/enabled', cached=True):
            # compile graph
            html = PopulateTemplate(pb, 'null', pb.dynamic_inclusions, pb.graph_full_page_template, content='')
            html = html.replace('{{navbar_links}}', '\n'.join(pb.navbar_links))\
                        .replace('{page_depth}', '2')

            op = pb.paths['html_output_folder'].joinpath('obs.html/graph/index.html')
            op.parent.mkdir(parents=True, exist_ok=True)

            with open(op, 'w', encoding="utf-8") as f:
                f.write(html)

        if pb.config.capabilities_needed['graph_data']:
            # add crosslinks to graph data
            pb.network_tree.AddCrosslinks()

            # Write node json to static folder
            CreateStaticFilesFolders(pb.paths['html_output_folder'])
            with open (pb.paths['html_output_folder'].joinpath('obs.html').joinpath('data/graph.json'), 'w', encoding="utf-8") as f:
                f.write(pb.network_tree.OutputJson())

        if pb.config.capabilities_needed['search_data']:
            
            # Compress search json and write to static folder
            gzip_path = pb.paths['html_output_folder'].joinpath('obs.html').joinpath('data/search.json.gzip')
            gzip_path.parent.mkdir(parents=True, exist_ok=True)
            gzip_content = pb.search.OutputJson()
            pb.gzip_hash = simpleHash(gzip_content)

            with gzip.open(gzip_path, 'wb', compresslevel=5) as f:
                f.write(gzip_content.encode('utf-8'))
            
        # Add Extra stuff to the output directories
        ExportStaticFiles(pb)

    print('< COMPILING HTML FROM MARKDOWN CODE: Done')

    if pb.gc('toggles/features/rss/enabled'):
        print('> COMPILING RSS FEED')
        feed = RssFeed(pb)
        feed.Compile()
        print('< COMPILING RSS FEED: Done')

    if pb.gc('file_exports'):
        file_exports = pb.gc('file_exports')
        if not isinstance(file_exports, list):
            raise Exception(f'Config value type of file_exports should be list, instead of {type(file_exports).__name__}.')

        print('> EXPORTING USER FILES')

        for ufile in file_exports:

            src =  pb.paths['obsidian_folder'].joinpath(ufile['src']).resolve()
            dst = pb.paths['html_output_folder'].joinpath(ufile['dst']).resolve()
            if not src.exists():
                raise Exception(f'File {src.as_posix()} not found')

            if 'encoding' not in ufile:
                encoding = 'utf-8'
            else:
                encoding = ufile['encoding']

            print(f"\tWriting {src.as_posix()} to {dst.as_posix()} ({encoding})")

            if encoding == 'binary':
                with open(src, 'rb') as f:
                    contents = f.read()  
                with open (dst, 'wb') as f:
                    f.write(contents)
            else:
                with open(src, 'r', encoding=encoding) as f:
                    contents = f.read()
                with open(dst, 'w', encoding=encoding) as f:
                    f.write(contents)

        print('< EXPORTING USER FILES: Done')

    print('\nYou can find your output at:')
    if pb.gc('toggles/compile_md'):
        print(f"\tmd: {pb.paths['md_folder']}")
    if pb.gc('toggles/compile_html'):
        print(f"\thtml: {pb.paths['html_output_folder']}")

@extra_info()
def recurseObisidianToMarkdown(fo:'OH_File', pb, log_level=1, iteration=0):
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
    # Don't follow links if this would exceed max note depth
    iteration += 1
    if pb.gc('max_note_depth') > -1 and iteration > pb.gc('max_note_depth'):
        return

    # Don't follow links when the user tells us not to
    if 'obs.html.tags' in md.metadata.keys() and 'leaf_note' in md.metadata['obs.html.tags']:
        return

    for lo in md.links:
        if lo == False or lo.processed_ntm == True:
            if pb.gc('toggles/verbose_printout', cached=True):
                if lo == False:
                    print('\t'*log_level, f"(ntm) Skipping converting {lo.link}, link not internal or not valid.")
                else:
                    print('\t'*log_level, f"(ntm) Skipping converting {lo.link}, already processed.")
            continue

        # Mark the file as processed so that it will not be processed again at a later stage
        lo.processed_ntm = True

        # Convert the note that is linked to
        if pb.gc('toggles/verbose_printout', cached=True):
            print('\t'*log_level, f"found link {lo.path['note']['file_absolute_path']} (through parent {fo.path['note']['file_absolute_path']})")

        pb.init_state(action='n2m', loop_type='note', current_fo=lo, subroutine='recurseObisidianToMarkdown')
        recurseObisidianToMarkdown(lo, pb, log_level=log_level, iteration=iteration)
        pb.reset_state()

@extra_info()
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

    page_depth = len(rel_dst_path.as_posix().split('/')) - 1

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
    node['id'] = GetNodeId(fo.path['markdown']['file_relative_path'].as_posix(), pb)
    if 'graph_name' in md.metadata.keys():
        node['name'] = md.metadata['graph_name']
    else:
        node['name'] = fo.path['markdown']['file_relative_path'].stem
        
    # Url is used so you can open the note/node by clicking on it
    node['url'] = pb.gc("html_url_prefix") + '/' + rel_dst_path.as_posix()
    node['rtr_url'] = rel_dst_path.as_posix()
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


    # Add page to search file
    # ------------------------------------------------------------------
    if pb.gc('toggles/features/search/enabled', cached=True):

        pb.search.AddPage(
            filename=page_path.stem, content=md.page, metadata=md.metadata, \
            url=node['url'], rtr_url=node['rtr_url'], title=node['name'] )

    # [1] Replace code blocks with placeholders so they aren't altered
    # They will be restored at the end
    # ------------------------------------------------------------------
    md.StripCodeSections()     

    # Get all local markdown links. 
    # ------------------------------------------------------------------
    # This is any string in between '](' and  ')' with no spaces in between the ( and )
    proper_links = re.findall(r'(?<=\]\()[^\s\]]+(?=\))', md.page)
    for l in proper_links:
        ol = l
        l = urllib.parse.unquote(l)

        # There is currently no way to match links containing parentheses, AND not matching the last ) in a link like ([test](link))
        if l.endswith(')'):
            l = l[:-1]

        # Init link
        link = MarkdownLink(pb, l, page_path, paths['md_folder'])

        # Don't process in the following cases (link empty or // in the link)
        if link.isValid == False or link.isExternal == True: 
            continue

        # [12] Copy non md files over wholesale, then we're done for that kind of file
        if link.fo is None:
            if link.suffix != '.md' and '/obs.html/dir_index.html' not in link.url:
                path_key = 'note'
                if not pb.gc('toggles/compile_md', cached=True):
                    path_key = 'markdown'
                print('\t'*(log_level+1), 'File ' + str(link.url) + ' not located, so not copied. @ ' + pb.state['current_fo'].path[path_key]['file_absolute_path'].as_posix())
        elif not link.fo.metadata['is_note']:
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
            new_link = f']({urllib.parse.quote(link.fo.get_link("html", origin=fo))}{query_part})'

        # Update link
        safe_link = re.escape(']('+ol+')')
        md.page = re.sub(safe_link, new_link, md.page)

    # [4] Handle local image links (copy them over to output)
    # ------------------------------------------------------------------
    for link in re.findall(r'\!\[.*?\]\((.*?)\)', md.page):
        
        l = urllib.parse.unquote(link)

        if l[0] == '/':
            l = l.replace('/', '', 1)

        # Only handle local image files (images located in the root folder)
        # Doublecheck, who knows what some weird '../../folder/..' does...
        rel_path_str, lo = FindFile(pb.files, l, pb)
        if rel_path_str == False:
            if pb.gc('toggles/warn_on_skipped_image', cached=True):
                warnings.warn(f"Image {l} treated as external and not imported in html")
            continue

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

        rel_path_str, lo = FindFile(pb.files, l, pb)
        if rel_path_str == False:
            if pb.gc('toggles/warn_on_skipped_image', cached=True):
                warnings.warn(f"Media {l} treated as external and not imported in html")
            continue

        # Copy src to dst
        lo.copy_file('mth')

        # [11.2] Adjust video link in page to new dst folder (when the link is to a file in our root folder)
        new_link = '<source src="'+urllib.parse.quote(lo.get_link('html', origin=fo))+'"'
        safe_link = r'<source src="'+re.escape(link)+r'"'
        md.page = re.sub(safe_link, new_link, md.page)

    # [?] Handle local embeddable tag-links (copy them over to output)
    # ------------------------------------------------------------------
    for link in re.findall(r'(?<=<embed src=")([^"]*)', md.page):
        l = urllib.parse.unquote(link)
        if '://' in l:
            continue

        rel_path_str, lo = FindFile(pb.files, l, pb)
        if rel_path_str == False:
            if pb.gc('toggles/warn_on_skipped_image', cached=True):
                warnings.warn(f"Media {l} treated as external and not imported in html")
            continue

        # Copy src to dst
        lo.copy_file('mth')

        # [11.2] Adjust video link in page to new dst folder (when the link is to a file in our root folder)
        new_link = '<embed src="'+urllib.parse.quote(lo.get_link('html', origin=fo))+'"'
        safe_link = r'<embed src="'+re.escape(link)+r'"'
        md.page = re.sub(safe_link, new_link, md.page)

    # [?] Documentation styling: Table of Contents
    # ------------------------------------------------------------------
    if pb.gc('toggles/features/styling/toc_pane', cached=True) or pb.gc('toggles/features/styling/add_toc', cached=True):
        # convert the common [[_TOC_]] into [TOC]
        md.page = md.page.replace('[[_TOC_]]', '[TOC]')

    if pb.gc('toggles/features/styling/add_toc', cached=True):
        if '[TOC]' not in md.page:
            # if h1 is present, place toc after the first h1, else put it at the top of the page.
            output = ''
            found_h1 = False
            for line in md.page.split('\n'):
                output += line + '\n'
                if found_h1 == False and line.startswith('# '):
                    output += '\n[TOC]\n\n'
                    found_h1 = True
            
            if found_h1:
                md.page = output
            else: 
                md.page = '\n[TOC]\n\n' + md.page

    # -- [8] Insert markdown links for bare http(s) links (those without the [name](link) format).
    # Cannot start with [, (, nor "
    # match 'http://* ' or 'https://* ' (end match by whitespace)
    # Note that note->md step also does this, this should be void if doing note-->html, but useful when doing md->html
    for l in re.findall("(?<![\[\(\"])(https*:\/\/.[^\s]*)", md.page):
        new_md_link = f"[{l}]({l})"
        safe_link = re.escape(l)
        md.page = re.sub(f"(?<![\[\(])({safe_link})", new_md_link, md.page)

    # [1] Restore codeblocks/-lines
    # ------------------------------------------------------------------
    md.RestoreCodeSections()

    # [11] Convert markdown to html
    # ------------------------------------------------------------------
    extensions = [
        'abbr', 'attr_list', 'def_list', 
        'fenced_code', 
        'md_in_html', FootnoteExtension(), FormattingExtension(), 
        'codehilite', 
        CustomTocExtension(), MermaidExtension(), CallOutExtension(), 'pymdownx.arithmatex']
    extension_configs = {
        'codehilite': {
            'linenums': False
        },
        'pymdownx.arithmatex': {
            'generic': True
        }
    }

    if pb.gc('toggles/features/dataview/enabled'):
        extensions.append('dataview')
        extension_configs['dataview'] = {
            'note_path': rel_dst_path,
            'dataview_export_folder': pb.paths['dataview_export_folder']
        }
        
    if pb.gc('toggles/features/eraser/enabled'):
        extensions.append(EraserExtension())

    if pb.gc('toggles/features/embedded_search/enabled'):
        extensions.append(EmbeddedSearchExtension())

    extensions.append(CodeWrapperExtension())
    extensions.append(AdmonitionExtension())
    #extensions.append('custom_tables')


    html_body = markdown.markdown(md.page, extensions=extensions, extension_configs=extension_configs)

    # HTML Tweaks
    # [??] Embedded note titles integration
    # ------------------------------------------------------------------
    if pb.config.capabilities_needed['embedded_note_titles']:
        title = node['name']

        # overwrite node name (titleMetadataField)
        if 'titleMetadataField' in pb.config.plugin_settings['embedded_note_titles'].keys():
            title_key = pb.config.plugin_settings['embedded_note_titles']['titleMetadataField']
            if title_key in node['metadata'].keys():
                title = node['metadata'][title_key]

        # hide if h1 is present
        hide = False
        if 'hideOnH1' in pb.config.plugin_settings['embedded_note_titles'].keys() and pb.config.plugin_settings['embedded_note_titles']['hideOnH1']:
            header_dict, root_element = ConvertMarkdownToHeaderTree(md.page)
            if len(root_element['content']) > 0 and isinstance(root_element['content'][0], dict) and root_element['content'][0]['level'] == 1:
                hide = True

        # hideOnMetadataField
        if 'hideOnMetadataField' in pb.config.plugin_settings['embedded_note_titles'].keys() and pb.config.plugin_settings['embedded_note_titles']['hideOnMetadataField']:
            if 'embedded-title' in node['metadata'].keys() and node['metadata']['embedded-title'] == False:
                hide = True 

        # add embedded title
        if not hide:
            html_body = f"<embeddedtitle>{title.capitalize()}</embeddedtitle>\n" + html_body 

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

    html_body += '\n<div class="note-footer">\n'

    # [??] breadcrumbs
    if pb.gc('toggles/features/breadcrumbs/enabled', cached=True):
        html_body = '{_obsidian_html_breadcrumbs_pattern_}\n' + html_body

    # [18] add backlinks to page 
    if pb.gc('toggles/features/backlinks/enabled', cached=True):
        html_body += '{_obsidian_html_backlinks_pattern_}\n'

    # [18] add tags to page 
    if pb.gc('toggles/features/tags_page/styling/show_in_note_footer', cached=True):
        html_body += '<div class="tags">\n{_obsidian_html_tags_footer_pattern_}\n</div>\n'    

    html_body += '\n</div>' #class="note-footer"

    # [17] Add in graph code to template (via {content})
    # This shows the "Show Graph" button, and adds the js code to handle showing the graph
    if pb.gc('toggles/features/graph/enabled', cached=True):
        graph_template = pb.graph_template.replace('{id}', simpleHash(html_body))\
                                       .replace('{pinnedNode}', node['id'])\
                                       .replace('{pinnedNodeGraph}', str(node['nid']))\
                                       .replace('{html_url_prefix}', html_url_prefix)\
                                       .replace('{graph_coalesce_force}', pb.gc('toggles/features/graph/coalesce_force', cached=True))\
                                       .replace('{graph_classes}', '')
        html_body += f"\n{graph_template}\n"

    # Add node_id to page so that we can fetch this in the second-pass
    html_body += '{_obsidian_html_node_id_pattern_:'+node['id']+'}\n'


    # [16] Wrap body html in valid html structure from template
    # ------------------------------------------------------------------
    html = PopulateTemplate(pb, node['id'], pb.dynamic_inclusions, pb.html_template, content=html_body)

    html = html.replace('{pinnedNode}', node['id'])\
               .replace('{html_url_prefix}', html_url_prefix)\
               .replace('{page_depth}', str(page_depth))\

    # [?] Documentation styling: Navbar
    # ------------------------------------------------------------------
    html = html.replace('{{navbar_links}}', '\n'.join(pb.navbar_links))  

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

        pb.init_state(action='m2h', loop_type='md_note', current_fo=lo, subroutine='ConvertMarkdownPageToHtmlPage')
        ConvertMarkdownPageToHtmlPage(lo, pb, backlinkNode, log_level=log_level)
        pb.reset_state()

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

    md += f'\n> [View all tags]({html_url_prefix}/obs.html/tags/index.html)'

    # Compile html
    extension_configs = {
        'codehilite': {
            'linenums': False
        },
        'pymdownx.arithmatex': {
            'generic': True
        }
    }    

    html_body = markdown.markdown(md, extensions=['extra', 'codehilite', 'obs_toc', 'mermaid', 'callout', 'pymdownx.arithmatex'], extension_configs=extension_configs)

    di = '<link rel="stylesheet" href="'+html_url_prefix+'/obs.html/static/taglist.css" />'

    html = PopulateTemplate(pb, 'none', pb.dynamic_inclusions, pb.html_template, html_url_prefix=html_url_prefix, content=html_body, dynamic_includes=di, container_wrapper_class_list=['single_tab_page-left-aligned'])

    html = html.replace('{pinnedNode}', 'tagspage')
    html = html.replace('{{navbar_links}}', '\n'.join(pb.navbar_links)) 
    html = html.replace('{left_pane_content}', '')\
               .replace('{right_pane_content}', '')
    
    # Write file
    tag_dst_path.parent.mkdir(parents=True, exist_ok=True)   
    with open(tag_dst_path_posix, 'w', encoding="utf-8") as f:
        f.write(html) 

    # Return link of this page, to be used by caller for building its page
    return rel_dst_path_as_posix
