from .NetworkTree import NetworkTree

class PicknickBasket:
    files = None           
    tagtree = None
    config = None
    paths = None
    html_template = None
    dynamic_inclusions = None

    def __init__(self, config, paths):
        self.config = config
        self.tagtree = {'notes': [], 'subtags': {}}
        self.paths = paths
        self.network_tree = NetworkTree(config)