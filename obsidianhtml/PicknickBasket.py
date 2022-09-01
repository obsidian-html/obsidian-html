from .NetworkTree import NetworkTree
from .ConfigManager import CheckConfigRecurse, MergeDictRecurse, Config
from .Search import SearchHead
from .CreateIndexFromDirStructure import CreateIndexFromDirStructure
import inspect


class PicknickBasket:
    state = None
    config = None
    verbose = None
    files = None
    tagtree = None
    paths = None
    html_template = None
    dynamic_inclusions = None
    gzip_hash = ''
    treeobj = None

    def __init__(self):
        self.tagtree = {'notes': [], 'subtags': {}}
        self.network_tree = NetworkTree(self.verbose)
        self.search = SearchHead()

        # State should be updated whenever we start a new type of operation.
        # When doing an operation by looping through notes, set loop_type to 'note', for links within a note 'note_link', if not in a loop-type operation, set to None.
        # This information is used to provide extra information to the user when an error does occur, primarily which note causes the error.
        # In the beginning not every action will update the state, call self.reset_state to unset the state so that we are not reporting stale information.
        self.state = {}
        self.reset_state()

    def reset_state(self):
        self.state['action'] = 'Unknown'
        self.state['main_function'] = None
        self.state['loop_type'] = None
        self.state['current_fo'] = None

    def init_state(self, **kwargs):
        self.reset_state()
        self.state['subroutine'] = inspect.stack()[1][3]    # this can be overwritten by caller by setting kwarg subroutine='<value>'
        for key in kwargs.keys():
            self.state[key] = kwargs[key]

    def loadConfig(self, input_yml_path_str=False):
        self.config = Config(self, input_yml_path_str)
        self.config.LoadIncludedFiles()

    def gc(self, path:str, cached=False):
        if cached:
            return self.config._get_config_cached(path)
        return self.config.get_config(path)

    def sc(self, path, value):
        return self.config.set_config(path, value)

    def add_file(self, rel_path, obj):
        #print(rel_path)
        self.files[rel_path] = obj

    def EnsureTreeObj(self):
        if self.treeobj is None:
            self.treeobj = CreateIndexFromDirStructure(self, self.paths['html_output_folder'])




