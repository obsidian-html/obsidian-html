from pathlib import Path

from .ConfigManager import Config, find_user_config_yaml_path
from .FileFinder import FileFinder
from ..features.Search import SearchHead
from ..features.CreateIndexFromDirStructure import CreateIndexFromDirStructure


class PicknickBasket:
    state = None  # used for debugging info, keeps track of what we are doing at each point in time
    config = None  # dict with all the config values
    verbose = None
    index = None  # contains the file tree and the network tree
    tagtree = None
    paths = None  # paths to input and output folders, as configured by user
    html_template = None
    dynamic_inclusions = None
    gzip_hash = ""
    treeobj = None
    jars = None  # dict with contents to store for later, see it as a cache
    user_config_dict = None  # fill with a dict to circumvent loading input yaml

    def __init__(self):
        self.tagtree = {"notes": [], "subtags": {}}
        self.jars = {}
        # self.network_tree = NetworkTree(self.verbose)
        self.search = SearchHead()

        self.FileFinder = FileFinder()

        # State should be updated whenever we start a new type of operation.
        # When doing an operation by looping through notes, set loop_type to 'note', for links within a note 'note_link', if not in a loop-type operation, set to None.
        # This information is used to provide extra information to the user when an error does occur, primarily which note causes the error.
        # In the beginning not every action will update the state, call self.reset_state to unset the state so that we are not reporting stale information.
        self.state = {}
        self.reset_state()

    def construct(self, config_yaml_location):
        # Load config, paths, etc
        self.loadConfig(config_yaml_location)
        self.set_paths()
        self.compile_dynamic_inclusions()
        self.config.load_embedded_titles_plugin()

    def reset_state(self):
        self.state["action"] = "Unknown"
        self.state["main_function"] = None
        self.state["loop_type"] = None
        self.state["current_fo"] = None

    def init_state(self, **kwargs):
        self.reset_state()
        # self.state['subroutine'] = inspect.stack()[1][3]    # this can be overwritten by caller by setting kwarg subroutine='<value>'
        self.state["subroutine"] = None
        for key in kwargs.keys():
            self.state[key] = kwargs[key]

    def loadConfig(self, config_yaml_location=""):
        # find correct config yaml
        if self.user_config_dict is None:
            input_yml_path_str = find_user_config_yaml_path(config_yaml_location)
        else:
            input_yml_path_str = ""

        # create config object based on config yaml
        self.config = Config(self, input_yml_path_str)

        # build up config object further
        self.config.LoadIncludedFiles()
        self.configured_html_prefix = self.gc("html_url_prefix")

    def set_paths(self):
        pb = self
        paths = {
            "obsidian_folder": Path(pb.gc("obsidian_folder_path_str")).resolve(),
            "md_folder": Path(pb.gc("md_folder_path_str")).resolve(),
            "obsidian_entrypoint": Path(pb.gc("obsidian_entrypoint_path_str")).resolve(),
            "md_entrypoint": Path(pb.gc("md_entrypoint_path_str")).resolve(),
            "html_output_folder": Path(pb.gc("html_output_folder_path_str")).resolve(),
        }
        paths["original_obsidian_folder"] = paths["obsidian_folder"]  # use only for lookups!
        paths["dataview_export_folder"] = paths["obsidian_folder"].joinpath(pb.gc("toggles/features/dataview/folder"))

        if pb.gc("toggles/extended_logging", cached=True):
            paths["log_output_folder"] = Path(pb.gc("log_output_folder_path_str")).resolve()

        # Deduce relative paths
        if pb.gc("toggles/compile_md", cached=True):
            paths["rel_obsidian_entrypoint"] = paths["obsidian_entrypoint"].relative_to(paths["obsidian_folder"])
        paths["rel_md_entrypoint_path"] = paths["md_entrypoint"].relative_to(paths["md_folder"])

        # Set paths
        pb.paths = paths

    def update_paths(self, reason, **kwargs):
        # If for any reason the paths need to be updated, this is the function to do it through
        if reason == "using_tmpdir":
            if "tmpdir" not in kwargs:
                raise Exception("tmpdir kwarg expected when updating paths because of using tmpdir!")
            # update paths
            self.paths["obsidian_folder"] = Path(kwargs.get("tmpdir").name).resolve()
            self.paths["obsidian_entrypoint"] = self.paths["obsidian_folder"].joinpath(self.paths["rel_obsidian_entrypoint"])
        else:
            raise Exception(f"path update reason {reason} unknown")

    def compile_dynamic_inclusions(self):
        # This is a set of javascript/css files to be loaded into the header based on config choices.
        dynamic_inclusions = ""
        try:
            dynamic_inclusions += "\n".join(self.gc("html_custom_inclusions")) + "\n"
        except:
            None
        self.dynamic_inclusions = dynamic_inclusions

        # This is a set of javascript/css files to be loaded into the footer based on config choices.
        dynamic_footer_inclusions = ""
        try:
            dynamic_footer_inclusions += "\n".join(self.gc("html_custom_footer_inclusions")) + "\n"
        except:
            None
        self.dynamic_footer_inclusions = dynamic_footer_inclusions

    def gc(self, path: str, cached=False):
        if cached:
            return self.config._get_config_cached(path)
        return self.config.get_config(path)

    def sc(self, path, value):
        return self.config.set_config(path, value)

    def EnsureTreeObj(self):
        if self.treeobj is None:
            self.treeobj = CreateIndexFromDirStructure(self, self.paths["html_output_folder"])
