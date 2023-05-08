import yaml
from pathlib import Path

from .ConfigManager import Config, find_user_config_yaml_path
from .FileFinder import FileFinder
from ..features.Search import SearchHead
from ..features.CreateIndexFromDirStructure import CreateIndexFromDirStructure

from ..modules import controller as module_controller


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
    module_data_folder = None  # integration with new control flow based on modules

    def __init__(self):
        self.tagtree = {"notes": [], "subtags": {}}
        self.jars = {}
        # self.network_tree = NetworkTree(self.verbose)

        self.search = SearchHead()
        self.FileFinder = FileFinder()
        self.ConfigManager = Config(self)
        self.plugin_settings = {"embedded_note_titles": {}}  # <- does nothing at the moment, should be factored out

        # State should be updated whenever we start a new type of operation.
        # When doing an operation by looping through notes, set loop_type to 'note', for links within a note 'note_link', if not in a loop-type operation, set to None.
        # This information is used to provide extra information to the user when an error does occur, primarily which note causes the error.
        # In the beginning not every action will update the state, call self.reset_state to unset the state so that we are not reporting stale information.
        self.state = {}
        self.reset_state()

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

    def gc(self, path: str, cached=False):
        if cached:
            return self.ConfigManager._get_config_cached(path)
        return self.ConfigManager.get_config(path)

    def sc(self, path, value):
        return self.ConfigManager.set_config(path, value)

    def EnsureTreeObj(self):
        if self.treeobj is None:
            self.treeobj = CreateIndexFromDirStructure(self, self.paths["html_output_folder"])
