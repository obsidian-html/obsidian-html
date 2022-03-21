from .NetworkTree import NetworkTree
from .ConfigManager import CheckConfigRecurse, MergeDictRecurse, Config


class PicknickBasket:
    config = None
    verbose = None
    files = None
    tagtree = None
    paths = None
    html_template = None
    dynamic_inclusions = None

    def __init__(self):
        self.tagtree = {'notes': [], 'subtags': {}}
        self.network_tree = NetworkTree(self.verbose)
    
    def loadConfig(self, input_yml_path_str=False):
        self.config = Config(self, input_yml_path_str)

    def gc(self, path:str, cached=False):
        if cached:
            return self.config._get_config_cached(path)
        return self.config.get_config(path)

    def sc(self, path, value):
        return self.config.set_config(path, value)



        





