import yaml
import glob
import os

from .lib import pushd, WriteFileLog
from .PathFinder import OH_File

class FileTree:
    def __init__(self, pb):
        self.pb = pb

    def load_file_tree(self):
        pb = self.pb
        self.pb.files = {}
        
        if pb.gc('toggles/compile_md', cached=True):
            root = pb.paths['obsidian_folder']
        else:
            root = pb.paths['md_folder']

        included_folders = pb.gc('included_folders')
        exclude_subfolders = pb.gc('exclude_glob')
        
        if pb.gc('toggles/verbose_printout'):
            print('> CREATING FILE TREE')

        # Check input
        if not isinstance(included_folders, list):
            raise Exception(f"Type of included_folders should be list, got {type(included_folders)}")
        if not isinstance(exclude_subfolders, list):
            raise Exception(f"Type of exclude_subfolders should be list, got {type(exclude_subfolders)}")

        # Get folders to look in
        input_folders = []
        if len(included_folders):
            for f in included_folders:
                p = root.joinpath(f)
                ps = p.resolve().as_posix()
                if not p.exists():
                    raise Exception(f"Included folder {f} does not exist (looked at {ps})")
                input_folders.append(p)
        else:
            rs = root.resolve().as_posix()
            if not root.exists():
                raise Exception(f"Given vault folder {root} does not exist (looked at {rs})")
            input_folders.append(root)  


        # Compile folder list to exclude
        owd = pushd(root)          # move working dir to root dir (needed for glob)

        excluded_folders = []
        for line in pb.gc('exclude_glob', cached=True):
            if line[0] != '/':
                line = '**/' + line
            else:
                line = line[1:]
            excluded_folders += [root.joinpath(x) for x in glob.glob(line, recursive=True)]
        excluded_folders = list(set(excluded_folders))
        
        os.chdir(owd)

        # Load files into pb.files
        for input_dir in input_folders:
            for path in input_dir.rglob('*'):
                get_file(path, root, excluded_folders, pb)

        # add index.md when converting straight from md to html
        if not pb.gc('toggles/compile_md', cached=True):
            print(root.joinpath('index.md'))
            get_file(root.joinpath('index.md'), root, excluded_folders, pb)

        # Done
        if pb.gc('toggles/verbose_printout', cached=True):
            print('< CREATING FILE TREE: Done')

        if pb.gc('toggles/extended_logging', cached=True):
            WriteFileLog(pb.files, pb.paths['log_output_folder'].joinpath('files.md'), include_processed=False)


def get_file(path, root, excluded_folders, pb):

    if path.is_dir():
        return

    # Exclude configured subfolders
    try:
        _continue = False
        for folder in excluded_folders:
            if path.resolve().is_relative_to(folder):
                if pb.gc('toggles/verbose_printout', cached=True):
                    print(f'\tExcluded folder {folder}: Excluded file {path.name}.')
                _continue = True
                break
        if _continue:
            return
    except:
        None

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
            fo.compile_metadata(fo.path['markdown']['file_absolute_path'].as_posix(), cached=True)

        # Add to tree
        pb.add_file(fo.path['note']['file_relative_path'].as_posix(), fo)
    else:
        # compile markdown --> html (based on the found markdown path)
        fo.init_markdown_path(path)
        fo.compile_metadata(fo.path['markdown']['file_absolute_path'], cached=True)

        # Add to tree
        pb.add_file(fo.path['markdown']['file_relative_path'].as_posix(), fo)


            
