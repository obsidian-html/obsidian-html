import glob
import os

from ...lib import pushd, WriteFileLog

from ...core.NetworkTree import NetworkTree
from ...core.FileObject import FileObject


from ..base_classes import ObsidianHtmlModule


class LoadFileTreeModule(ObsidianHtmlModule):
    """
    This module will create the files.yml file, which lists all the files in the source folder (vault or md folder), minus the excluded files.
    It will also create the aliased_files.yml file, which contains references to files by an alias.
    """

    @property
    def requires(self):
        return tuple()

    @property
    def provides(self):
        return tuple(["files.yml", "aliased_files.yml"])

    @property
    def alters(self):
        return tuple()

    def accept(self, module_data_folder):
        """This function is run before run(), if it returns False, then the module run is skipped entirely. Any other value will be accepted"""
        return
        
    def run(self):
        # TODO: rewrite
        # get input folder
        if self.gc("toggles/compile_md", cached=True):
            self.input_folder_root = self.pb.paths["obsidian_folder"]
        else:
            self.input_folder_root = self.pb.paths["md_folder"]


# class Index:
#     def __init__(self, pb):
#         # integrate with picknickbasket
#         self.pb = pb
#         self.pb.index = self

#         # setup network tree, which keeps track of the graph (nodes and the links between them)
#         self.network_tree = NetworkTree(self)

#         # setup the file tree, which provides detailed information on the files in the vault/output folders
#         self.init_file_tree()
#         self.import_files_into_file_tree()

#     def init_file_tree(self):
#         """This method sets up everything needed for the file tree. It does not yet load the files into the file tree"""
#         self.files = {}  # contains every file exactly once (currently twice in the case of the index file)
#         self.aliased_files = {}  # files known under a different path_key, such as for slugged file paths
#         self.excluded_folders = []
#         self.included_folders = []
#         self.input_folder_root = ""

#         self.set_input_folder_root()
#         self.compile_excluded_folder_list()
#         self.compile_included_folder_list()

#     def compile_html_relpath_lookup_table(self):
#         self.fo_by_html_relpath = {}
#         for fo in self.files.values():
#             rel_path = fo.path["html"]["file_relative_path"].as_posix()
#             self.fo_by_html_relpath[rel_path] = fo

#     def import_files_into_file_tree(self):
#         """This method reads all the files in the input folders - minus the excluded files - converts them into file objects, and puts them in the self.files dict"""
#         pb = self.pb
#         root = self.input_folder_root

#         if self.pb.gc("toggles/verbose_printout"):
#             print("> CREATING FILE TREE")

#         # Load files into pb.index.files
#         for input_dir in self.included_folders:
#             for path in input_dir.rglob("*"):
#                 self.convert_file_to_file_object_and_add_to_file_tree(path, root, self.excluded_folders, pb)

#         # add index.md when converting straight from md to html
#         if not pb.gc("toggles/compile_md", cached=True):
#             print(root.joinpath("index.md"))
#             self.convert_file_to_file_object_and_add_to_file_tree(root.joinpath("index.md"), root, self.excluded_folders, pb)

#         # Done
#         if pb.gc("toggles/verbose_printout", cached=True):
#             print("< CREATING FILE TREE: Done")

#         if pb.gc("toggles/extended_logging", cached=True):
#             WriteFileLog(pb.index.files, pb.paths["log_output_folder"].joinpath("files.md"), include_processed=False)

#     def convert_file_to_file_object_and_add_to_file_tree(self, path, root, excluded_folders, pb):
#         if path.is_dir():
#             return

#         # Exclude configured subfolders
#         try:
#             _continue = False
#             for folder in excluded_folders:
#                 if path.resolve().is_relative_to(folder):
#                     if pb.gc("toggles/verbose_printout", cached=True):
#                         print(f"\tExcluded folder {folder}: Excluded file {path.name}.")
#                     _continue = True
#                     break
#             if _continue:
#                 return
#         except:
#             None

#         # Create object to help with handling all the info on the file
#         fo = FileObject(pb)

#         # Compile paths
#         if pb.gc("toggles/compile_md", cached=True):
#             # compile note --> markdown
#             fo.init_note_path(path)
#             fo.compile_metadata(fo.path["note"]["file_absolute_path"], cached=True)

#             if pb.gc("toggles/compile_html", cached=True):
#                 # compile markdown --> html (based on the given note path)
#                 fo.init_markdown_path()
#                 fo.compile_metadata(fo.path["markdown"]["file_absolute_path"].as_posix(), cached=True)

#             # Add to tree
#             self.add_file_object_to_file_tree(fo.path["note"]["file_relative_path"].as_posix(), fo)
#         else:
#             # compile markdown --> html (based on the found markdown path)
#             fo.init_markdown_path(path)
#             fo.compile_metadata(fo.path["markdown"]["file_absolute_path"], cached=True)

#             # Add to tree
#             self.add_file_object_to_file_tree(fo.path["markdown"]["file_relative_path"].as_posix(), fo)

#     def add_file_object_to_file_tree(self, rel_path, obj):
#         if self.pb.gc("toggles/force_filename_to_lowercase", cached=True):
#             rel_path = rel_path.lower()
#         self.files[rel_path] = obj

#     def set_input_folder_root(self):
#         if self.pb.gc("toggles/compile_md", cached=True):
#             self.input_folder_root = self.pb.paths["obsidian_folder"]
#         else:
#             self.input_folder_root = self.pb.paths["md_folder"]

#     def compile_excluded_folder_list(self):
#         """This function converts the glob patterns to a simple list of folders to exclude"""

#         # Test input
#         exclude_subfolders = self.pb.gc("exclude_glob")
#         if not isinstance(exclude_subfolders, list):
#             raise Exception(f"Type of exclude_subfolders should be list, got {type(exclude_subfolders)}")

#         # move working dir to root dir (needed for glob to work)
#         owd = pushd(self.input_folder_root)

#         # find all excluded folders
#         excluded_folders = []
#         for line in exclude_subfolders:
#             if line[0] != "/":
#                 line = "**/" + line
#             else:
#                 line = line[1:]
#             excluded_folders += [self.input_folder_root.joinpath(x) for x in glob.glob(line, recursive=True)]

#         # remove duplicate and store result
#         self.excluded_folders = list(set(excluded_folders))

#         # back to original working directory
#         os.chdir(owd)

#     def compile_included_folder_list(self):
#         """Compile given rtr paths to absolute posix string paths, and test if they exist. If no input folders given, just list the root itself"""
#         root = self.input_folder_root

#         # Check input
#         included_folders = self.pb.gc("included_folders")
#         if not isinstance(included_folders, list):
#             raise Exception(f"Type of included_folders should be list, got {type(included_folders)}")

#         # Convert to abs path list
#         input_folders = []
#         if len(included_folders):
#             for f in included_folders:
#                 p = root.joinpath(f)
#                 ps = p.resolve().as_posix()
#                 if not p.exists():
#                     raise Exception(f"Included folder {f} does not exist (looked at {ps})")
#                 input_folders.append(p)
#         # Just use root as input folder
#         else:
#             rs = root.resolve().as_posix()
#             if not root.exists():
#                 raise Exception(f"Given vault folder {root} does not exist (looked at {rs})")
#             input_folders.append(root)

#         self.included_folders = input_folders
