from pathlib import Path
import yaml
from .lib import PopulateTemplate, OpenIncludedFile

class CreateIndexFromDirStructure():
    def __init__(self, pb, path):
        self.pb = pb
        self.root = path

        self.exclude_subfolders = pb.gc('toggles/features/create_index_from_dir_structure/exclude_subfolders')
        self.exclude_files = pb.gc('toggles/features/create_index_from_dir_structure/exclude_files')
        self.rel_output_path = pb.gc('toggles/features/create_index_from_dir_structure/rel_output_path')
        
        if pb.gc('toggles/relative_path_html'):
            self.html_url_prefix = pb.sc(path='html_url_prefix', value='..')
        else:
            self.html_url_prefix = pb.gc("html_url_prefix")

        self.verbose = pb.gc('toggles/verbose_printout')

        self.tree = self.get_tree(path)
        self.tree = self.build_tree_recurse(self.tree)
        self.sort_tree()

        # used in BuildIndex
        self.uid = 0
        self.html = ''


    def get_tree(self, path, files=None, folders=None):
        if files is None:
            files = []
        if folders is None:
            folders = []

        if isinstance(path, str):
            path = Path(path).resolve()

        return {
            'name': path.name, 
            'path': path.as_posix(),
            'folders':folders, 
            'files':files
        }

    def build_tree_recurse(self, tree):
        verbose = self.verbose

        for path in Path(tree['path']).resolve().glob('*'):
            # Exclude configured subfolders
            _continue = False
            for folder in self.exclude_subfolders:
                excl_folder_path = self.root.joinpath(folder)
                if path.resolve().is_relative_to(excl_folder_path):
                    if verbose:
                        print(f'\tExcluded folder {excl_folder_path}: Excluded file {path.name}.')
                    _continue = True
                    break
            if _continue:
                continue


            # for dir: create a subtree
            if path.is_dir():
                new_branch = self.build_tree_recurse(self.get_tree(path))
                tree['folders'].append(new_branch)
                continue

            # exclude files
            for ef in self.exclude_files:
                excl_file_path = self.root.joinpath(ef)
                if excl_file_path == path:
                    if verbose:
                        print(f'\tExcluded file {excl_file_path}.')
                    _continue = True
                    break
            if _continue:
                continue

            # append file
            tree['files'].append({'name': path.stem, 'path': path.as_posix()})

        return tree

    def sort_tree(self):
        def _recurse(tree):
            tree['folders'] = sorted(tree['folders'], key=lambda d: d['name'])
            tree['files'] = sorted(tree['files'], key=lambda d: d['name'])
            for folder in tree['folders']:
                _recurse(folder)
        _recurse(self.tree)

    def in_tree(self, path, subpath):
        path_parts = [x for x in path.split('/') if x]
        subpath_parts = [x for x in subpath.split('/') if x]

        if len(subpath_parts) > len(path_parts):
            return False

        for i, part in enumerate(subpath_parts):
            if part != path_parts[i]:
                return False
        
        return True

    def get_dir(self, path):
        return '/'+'/'.join([x for x in path.split('/') if x][:-1])

    def BuildIndex(self, current_page='/'):
        def _recurse(tree, tab_level, path, current_page):
            current_dir = self.get_dir(current_page)
            html = ''

            dir_active = ''
            if self.in_tree(current_dir, path):
                dir_active = 'active'

            if tab_level >= 0:
                #print('\t'*tab_level, tree['name'])
                html += '\t'*tab_level + f'<button id="folder-{self.uid}" class="dir-button" onclick="toggle_dir(this.id)">{tree["name"]}</button>\n'
                html += '\t'*tab_level + f'<div id="folder-container-{self.uid}" class="dir-container requires_js {dir_active}" path="{path}">\n'
            tab_level += 1
            self.uid += 1

            for folder in tree['folders']:
                html += _recurse(folder, tab_level, '/'.join( (path, folder['name']) ), current_page)

            html += '\t'*tab_level + '<ul class="dir-list">\n'
            tab_level += 1

            excluded_paths = self.pb.gc('toggles/features/create_index_from_tags/exclude_paths', cached=True)

            for f in tree['files']:
                rel_path = Path(f['path']).resolve().relative_to(self.root).as_posix()

                if rel_path in excluded_paths:
                    continue

                file_active = ''
                if '/'+rel_path == current_page:
                    file_active = 'active'
                
                # get link adjustment code
                class_list = ''
                external_blank_html = ''
                if Path(rel_path).suffix != '.html':
                    class_list = 'class="external-link"'
                    if self.pb.gc('toggles/external_blank'):
                        external_blank_html = 'target=\"_blank\" '
                
                html += '\t'*tab_level + f'<li><a class="{file_active}" href="{self.html_url_prefix}/{rel_path}" {external_blank_html} {class_list}>{f["name"]}</a></li>\n'
            
            tab_level -= 1
            html += '\t'*tab_level + '</ul>\n'
            tab_level -= 1
            if tab_level >= 0:
                html += '\t'*tab_level + '</div>\n'

            return html
        
        self.uid = 0
        html = _recurse(self.tree, -1, ''+self.html_url_prefix, current_page)

        return html

    def WriteIndex(self):
        output_path = self.root.joinpath(self.rel_output_path).resolve()

        # make parent folders if necessary
        output_path.parent.mkdir(exist_ok=True)

        # write html to output
        pb = self.pb
        
        html = PopulateTemplate(pb, 'none', pb.dynamic_inclusions, pb.html_template, content=self.html, container_wrapper_class_list=['single_tab_page-left-aligned'])

        html = html.replace('{pinnedNode}', 'dirtree')\
                   .replace('{left_pane_content}', '')\
                   .replace('{right_pane_content}', '')
    
        navbar_links = self.pb.gc('navbar_links', cached=True)
        elements = []
        for l in navbar_links:
            el = f'<a class="navbar-link"href="{self.html_url_prefix}/{l["link"]}" title="{l["name"]}">{l["name"]}</a>'
            elements.append(el)
        html = html.replace('{{navbar_links}}', '\n'.join(elements)) 


        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)








