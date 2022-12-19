import yaml
import glob
import os
from time import sleep

from .lib import pushd, WriteFileLog
from .PathFinder import OH_File

class FileTree:
    def __init__(self, pb):
        
        self.root = ''
        self.excluded_folders = []
        self.included_folders = []

        self.pb = pb
        self.pb.file_tree = self
        self.files = {}
        self.pb.files = self.files

        self.set_root()
        self.compile_excluded_folder_list()
        self.compile_included_folder_list()

    def add_file(self, rel_path, obj):
        if self.pb.gc('toggles/force_filename_to_lowercase', cached=True):
            rel_path = rel_path.lower()

        self.files[rel_path] = obj

    def load_file_tree(self):
        pb = self.pb
        root = self.root
        
        if pb.gc('toggles/verbose_printout'):
            print('> CREATING FILE TREE')

        # Load files into pb.files
        for input_dir in self.included_folders:
            for path in input_dir.rglob('*'):
                get_file(path, root, self.excluded_folders, pb)

        # add index.md when converting straight from md to html
        if not pb.gc('toggles/compile_md', cached=True):
            print(root.joinpath('index.md'))
            get_file(root.joinpath('index.md'), root, self.excluded_folders, pb)

        # Done
        if pb.gc('toggles/verbose_printout', cached=True):
            print('< CREATING FILE TREE: Done')

        if pb.gc('toggles/extended_logging', cached=True):
            WriteFileLog(pb.files, pb.paths['log_output_folder'].joinpath('files.md'), include_processed=False)

    def set_root(self):
        if self.pb.gc('toggles/compile_md', cached=True):
            self.root = self.pb.paths['obsidian_folder']
        else:
            self.root = self.pb.paths['md_folder']

    def compile_excluded_folder_list(self):
        ''' This function converts the glob patterns to a simple list of folders to exclude '''

        # Test input
        exclude_subfolders = self.pb.gc('exclude_glob')
        if not isinstance(exclude_subfolders, list):
            raise Exception(f"Type of exclude_subfolders should be list, got {type(exclude_subfolders)}")

        # move working dir to root dir (needed for glob to work)
        owd = pushd(self.root)          

        # find all excluded folders
        excluded_folders = []
        for line in exclude_subfolders:
            if line[0] != '/':
                line = '**/' + line
            else:
                line = line[1:]
            excluded_folders += [self.root.joinpath(x) for x in glob.glob(line, recursive=True)]

        # remove duplicate and store result
        self.excluded_folders = list(set(excluded_folders))

        # back to original working directory
        os.chdir(owd)

    def compile_included_folder_list(self):
        ''' Compile given rtr paths to absolute posix string paths, and test if they exist. If no input folders given, just list the root itself '''
        root = self.root

        # Check input
        included_folders = self.pb.gc('included_folders')
        if not isinstance(included_folders, list):
            raise Exception(f"Type of included_folders should be list, got {type(included_folders)}")

        # Convert to abs path list
        input_folders = []
        if len(included_folders):
            for f in included_folders:
                p = root.joinpath(f)
                ps = p.resolve().as_posix()
                if not p.exists():
                    raise Exception(f"Included folder {f} does not exist (looked at {ps})")
                input_folders.append(p)
        # Just use root as input folder
        else:
            rs = root.resolve().as_posix()
            if not root.exists():
                raise Exception(f"Given vault folder {root} does not exist (looked at {rs})")
            input_folders.append(root)  

        self.included_folders = input_folders


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
        pb.file_tree.add_file(fo.path['note']['file_relative_path'].as_posix(), fo)
    else:
        # compile markdown --> html (based on the found markdown path)
        fo.init_markdown_path(path)
        fo.compile_metadata(fo.path['markdown']['file_absolute_path'], cached=True)

        # Add to tree
        pb.file_tree.add_file(fo.path['markdown']['file_relative_path'].as_posix(), fo)


            
