from math import fabs
from .NetworkTree import NetworkTree
from . import printHelpAndExit
from .lib import OpenIncludedFile

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
        self.config = self.MergeDictRecurse(default_config, input_config)

        # Check if required input is missing
        self.CheckConfigRecurse(self.config)

        # Overwrite conf for verbose from command line
        # (If -v is passed in, __init__.py will set self.verbose to true)
        if self.verbose is not None:
            self.config['toggles']['verbose_printout'] = self.verbose
        else:
            self.verbose = self.config['toggles']['verbose_printout']

    # previously getConf()
    def gc(self, *keys:str):
        value = self.config.copy()
        for key in keys:
            value = value[key]
        return value

    def MergeDictRecurse(self, base_dict, update_dict, path=''):
        helptext = '\n\nTip: Run obsidianhtml -gc to see all configurable keys and their default values.\n'

        for k, v in update_dict.items():
            key_path = '/'.join(x for x in (path, k) if x !='')

            # every configured key should be known in base config, otherwise this might suggest a typo/other error
            if k not in base_dict.keys():
                raise Exception(f'\n\tThe configured key "{key_path}" is unknown. Check for typos/indentation. {helptext}')

            # don't overwrite a dict in the base config with a string, or something else
            # in general, we don't expect types to change
            if type(base_dict[k]) != type(v):
                raise Exception(f'\n\tThe value of key "{key_path}" is expected to be of type {type(base_dict[k])}, but is of type {type(v)}. {helptext}')

            # dict match -> recurse
            if isinstance(base_dict[k], dict) and isinstance(v, dict):
                base_dict[k] = self.MergeDictRecurse(base_dict[k], update_dict[k], path=key_path)
                continue
            
            # other cases -> copy over
            if isinstance(update_dict[k], list):
                base_dict[k] = v.copy()
            else:
                base_dict[k] = v

        return base_dict.copy()

    def CheckConfigRecurse(self, config, path='', match_str='<REQUIRED_INPUT>'):
        helptext = '\n\nTip: Run obsidianhtml -gc to see all configurable keys and their default values.\n'

        for k, v in config.items():
            key_path = '/'.join(x for x in (path, k) if x !='')
            
            if isinstance(v, dict):
                self.CheckConfigRecurse(config[k], path=key_path)

            if v == match_str:
                raise Exception(f'\n\tKey "{key_path}" is required. {helptext}')



