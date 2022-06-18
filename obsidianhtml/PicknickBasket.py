from .NetworkTree import NetworkTree
from .ConfigManager import CheckConfigRecurse, MergeDictRecurse, Config
from .Search import SearchHead


class PicknickBasket:
    config = None
    verbose = None
    files = None
    tagtree = None
    paths = None
    html_template = None
    dynamic_inclusions = None
    gzip_hash = ''

    def __init__(self):
        self.tagtree = {'notes': [], 'subtags': {}}
        self.network_tree = NetworkTree(self.verbose)
        self.search = SearchHead()
    
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


        





