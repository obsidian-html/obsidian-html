from math import fabs
from .NetworkTree import NetworkTree
from . import printHelpAndExit
from .lib import OpenIncludedFile, CheckConfigRecurse, MergeDictRecurse

import yaml

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
        # Make sure the user passes in a config file
        if input_yml_path_str == False:
            print('ERROR: No config file passed in. Use -i <path/to/config.yml> to pass in a config yaml.')
            printHelpAndExit(1)

        # Load default yaml first
        default_config = yaml.safe_load(OpenIncludedFile('defaults_config.yml'))

        # Load input yaml
        try:
            with open(input_yml_path_str, 'rb') as f:
                input_config =yaml.safe_load(f.read())
        except FileNotFoundError:
            print(f'Could not locate the config file {input_yml_path_str}.\n  Please try passing the exact location of it with the `obsidianhtml -i /your/path/to/{input_yml_path_str}` parameter.')
            printHelpAndExit(1)

        # Merge configs
        self.config = MergeDictRecurse(default_config, input_config)

        # Check if required input is missing
        CheckConfigRecurse(self.config)

        # Overwrite conf for verbose from command line
        # (If -v is passed in, __init__.py will set self.verbose to true)
        if self.verbose is not None:
            self.config['toggles']['verbose_printout'] = self.verbose
        else:
            self.verbose = self.config['toggles']['verbose_printout']

    # previously getConf()
    def gc(self, *keys:str):
        value = self.config
        path = []
        for key in keys:
            path.append(key)
            try:
                value = value[key]
            except KeyError:
                raise Exception(f"INTERNAL ERROR: Config setting '{'/'.join(path)}' not found in config.")
        return value





