from math import fabs
from .NetworkTree import NetworkTree

class PicknickBasket:
    verbose = None
    files = None
    tagtree = None
    paths = None
    html_template = None
    dynamic_inclusions = None

    def __init__(self, verbose, paths):
        self.verbose = verbose
        self.tagtree = {'notes': [], 'subtags': {}}
        self.paths = paths
        self.network_tree = NetworkTree(self.verbose)