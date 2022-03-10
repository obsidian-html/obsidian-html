from .lib import IsValidLocalMarkdownLink
from .MarkdownPage import MarkdownPage
import urllib.parse         # convert link characters like %

import frontmatter
from pathlib import Path 
import platform
import datetime

def CreateIndexFromTags(pb):
    # get settings
    paths = pb.paths
    files = pb.files
    settings = pb.gc('toggles','features','create_index_from_tags')

    method          = settings['sort']['method']
    key_path        = settings['sort']['key_path']
    value_prefix    = settings['sort']['value_prefix']
    sort_reverse    = settings['sort']['reverse']
    none_on_bottom  = settings['sort']['none_on_bottom']

    if pb.gc('toggles','verbose_printout'):
        print('> FEATURE: CREATE INDEX FROM TAGS: Enabled')

    # Test input
    if not isinstance(settings['tags'], list):
        raise Exception("toggles/features/create_index_from_tags/tags should be a list")

    if len(settings['tags']) == 0:
        raise Exception("Feature create_index_from_tags is enabled, but no tags were listed")

    # We'll need to write a file to the obsidian folder
    # This is not good if we don't target the temp folder (copy_vault_to_tempdir = True)
    # Because we don't want to mess around in people's vaults.
    # So disable this feature if that setting is turned off
    if pb.gc('copy_vault_to_tempdir') == False:
        raise Exception("The feature 'CREATE INDEX FROM TAGS' needs to write an index file to the obsidian path. We don't want to write in your vault, so in order to use this feature set 'copy_vault_to_tempdir: True' in your config.")

    # shorthand 
    include_tags = settings['tags']
    if pb.gc('toggles','verbose_printout'):
        print('\tLooking for tags: ', include_tags)


    # overwrite defaults
    index_dst_path = paths['obsidian_folder'].joinpath('__tags_index.md').resolve()

    if pb.gc('toggles','verbose_printout'):
        print('\tWill write the note index to: ', index_dst_path)
        print('\tWill overwrite entrypoints: obsidian_entrypoint, rel_obsidian_entrypoint')

    paths['obsidian_entrypoint']         = index_dst_path
    paths['rel_obsidian_entrypoint']     = paths['obsidian_entrypoint'].relative_to(paths['obsidian_folder'])
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

            # Check for each of the tags if its present
            # Skip if none matched
            matched = False
            for t in include_tags:
                if t in metadata['tags']:
                    if pb.gc('toggles','verbose_printout'):
                        print(f'\t\tMatched note {k} on tag {t}')
                    matched = True
            
            if matched == False:
                continue

            # get graphname of the page, we need this later
            graph_name = k[:-3]
            if 'graph_name' in metadata.keys():
                graph_name = metadata['graph_name']

            # determine sorting value
            sort_value   = None
            if method not in ('none', 'creation_time', 'modified_time'):
                if method == 'key_value':
                    # key can be multiple levels deep, like this: level1:level2
                    # get the value of the key
                    key_found = True
                    value = metadata
                    for key in key_path.split(':'):
                        if key not in value.keys():
                            key_found = False
                            break
                        value = value[key]
                    # only continue if the key is found in the current note, otherwise the 
                    # default sort value of None is kept
                    if key_found:
                        # for a list find all items that start with the value prefix
                        # then remove the value_prefix, and check if we have 1 item left
                        if isinstance(value, list):
                            items = [x.replace(value_prefix, '', 1) for x in value if x.startswith(value_prefix)]
                            if len(items) == 1:
                                sort_value = items[0]
                                # done
                        if isinstance(value, str):
                            sort_value = value.replace(value_prefix, '', 1)
                        if isinstance(value, bool):
                            sort_value = str(int(value))
                        if isinstance(value, int) or isinstance(value, float):
                            sort_value = str(value)
                        if isinstance(value, datetime.datetime):
                            sort_value = value.isoformat()
                else:
                    raise Exception(f'Sort method {method} not implemented. Check spelling.')
            
            # Get sort_value from files dict
            if method in ('creation_time', 'modified_time'):
                # created time is not really accessible under Linux, we might add a case for OSX
                if method == 'creation_time' and platform.system() != 'Windows' and platform.system() != 'Darwin':
                    raise Exception(f'Sort method of "create_time" under toggles/features/create_index_from_tags/sort/method is not available under {platform.system()}, only Windows.')
                sort_value = files[k][method]

            if pb.gc('toggles','verbose_printout'):
                print(f'\t\t\tSort value of note {k} is {sort_value}')

            # Add an entry into index_dict for each tag matched on this page
            for t in include_tags:
                if t in metadata['tags']:
                    # copy file to temp filetree for checking later
                    _files[k] = files[k].copy()

                    # Add entry to our index dict so we can parse this later
                    md = MarkdownPage(page_path, paths['obsidian_folder'], files)
                    md.SetDestinationPath(paths['html_output_folder'], paths['md_entrypoint'])
                    index_dict[t].append(
                        {
                            'file_key': k, 
                            'md_rel_path_str': md.rel_dst_path.as_posix(),
                            'graph_name': graph_name,
                            'sort_value': sort_value
                        }
                    )

    if len(_files.keys()) == 0:
        raise Exception(f"No notes found with the given tags.")

    if pb.gc('toggles','verbose_printout'):
        print(f'\tBuilding index.md')

    index_md_content = f'# {pb.gc("site_name")}\n'
    for t in index_dict.keys():
        # Add header
        index_md_content += f'## {t}\n'

        # shorthand
        notes = index_dict[t]

        # fill in none types
        # - get max value
        input_val = ''
        max_val = ''
        for n in notes:
            if n['sort_value'] is None:
                continue
            if n['sort_value'] > max_val:
                max_val = n['sort_value']
        max_val += 'Z'

        # - determine if we need to give max val or min val
        if none_on_bottom:
            input_val = max_val
            if sort_reverse:
                input_val = ''
        else:
            input_val = ''
            if sort_reverse:
                input_val = max_val
        
        # - fill in none types
        for n in notes:
            if n['sort_value'] is None:
                n['sort_value'] = input_val

        # Sort notes
        notes = sorted(index_dict[t], key=lambda note: note['sort_value'], reverse=sort_reverse)

        # Add to index content
        for n in notes:
            index_md_content += f'- [[{n["file_key"][:-3]}]]\n'
        index_md_content += '\n'

    # write content to markdown file
    with open(index_dst_path, 'w', encoding="utf-8") as f:
        f.write(index_md_content)

    # add file to file tree
    now = datetime.datetime.now().isoformat()
    pb.files['__tags_index.md'] = {'fullpath': str(index_dst_path), 'processed': False, 'pathobj': index_dst_path, 'creation_time': now, 'modified_time': now}

    # [17] Build graph node/links
    if pb.gc('toggles','features','create_index_from_tags','add_links_in_graph_tree'):

        if pb.gc('toggles','verbose_printout'):
            print(f'\tAdding graph links between index.md and the matched notes')
        
        node = pb.network_tree.NewNode()
        node['id'] = 'index'
        node['url'] = f'{pb.gc("html_url_prefix")}/index.html'
        pb.network_tree.AddNode(node)
        bln = node
        for t in index_dict.keys():
            for n in index_dict[t]:
                node = pb.network_tree.NewNode()
                node['id'] = n['graph_name']
                node['url'] = f'{pb.gc("html_url_prefix")}/{n["md_rel_path_str"][:-3]}.html'
                pb.network_tree.AddNode(node)

                link = pb.network_tree.NewLink()
                link['source'] = bln['id']
                link['target'] = node['id']
                pb.network_tree.AddLink(link)

    if pb.gc('toggles','verbose_printout'):
        print('< FEATURE: CREATE INDEX FROM TAGS: Done')

    return pb