from . import printHelpAndExit
from .lib import OpenIncludedFile

import inspect
import yaml
from functools import cache

class Config:
    config = None
    pb = None

    def __init__(self, pb, input_yml_path_str=False):
        self.pb = pb

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
        if self.pb.verbose is not None:
            self.config['toggles']['verbose_printout'] = self.pb.verbose
        else:
            self.pb.verbose = self.config['toggles']['verbose_printout']

        # Set toggles/no_tabs
        layout = self.config['toggles']['features']['styling']['layout']
        if layout == 'tabs':
            self.config['toggles']['no_tabs'] = False
        else:
            self.config['toggles']['no_tabs'] = True

        # Set main css file
        self.config['_css_file'] = f'main_{layout}.css'

    def verbose(self):
        return self.config['toggles']['verbose_printout']

    def disable_feature(self, feature_key_name):
        self.config['toggles']['features'][feature_key_name]['enabled'] = False

    @cache
    def _feature_is_enabled_cached(self, feature_key_name):
        return self.config['toggles']['features'][feature_key_name]['enabled']

    def feature_is_enabled(self, feature_key_name, cached=False):
        if cached:
            return self._feature_is_enabled_cached(feature_key_name)
        else:
            return self.config['toggles']['features'][feature_key_name]['enabled']

    @cache
    def _get_config_cached(self, path:str):
        return self.get_config(path)

    def get_config(self, path:str):
        keys = [x for x in path.split('/') if x != '']

        value = self.config
        path = []
        for key in keys:
            path.append(key)
            try:
                value = value[key]
            except KeyError:
                print(path)
                raise Exception(f"INTERNAL ERROR: Config setting '{'/'.join(path)}' not found in config.")
        return value

    # Set config
    def set_config(self, path:str, value):
        keys = [x for x in path.split('/') if x != '']

        # find key
        ptr = self.config
        ptr_path = []
        for key in keys[:-1]:
            ptr_path.append(key)
            try:
                ptr = ptr[key]
            except KeyError:
                raise Exception(f"INTERNAL ERROR: Config setting '{'/'.join(keys)}' not found in config. (Failed at {ptr_path})")
        ptr[keys[-1]] = value  
        return self.get_config(path)

    @cache
    def GetCachedConfig(self, descriptor):
        if descriptor == 'rss_show_icon':
            return (self.pb.gc('toggles/features/rss/enabled') and self.pb.gc('toggles/features/rss/styling/show_icon'))

        elif descriptor == 'dirtree_show_icon':
            return (self.pb.gc('toggles/features/create_index_from_dir_structure/enabled') and self.pb.gc('toggles/features/create_index_from_dir_structure/styling/show_icon'))


def MergeDictRecurse(base_dict, update_dict, path=''):
    helptext = '\n\nTip: Run obsidianhtml -gc to see all configurable keys and their default values.\n'

    for k, v in update_dict.items():
        key_path = '/'.join(x for x in (path, k) if x !='')

        # every configured key should be known in base config, otherwise this might suggest a typo/other error
        if k not in base_dict.keys():
            raise Exception(f'\n\tThe configured key "{key_path}" is unknown. Check for typos/indentation. {helptext}')

        # don't overwrite a dict in the base config with a string, or something else
        # in general, we don't expect types to change
        if type(base_dict[k]) != type(v):
            if base_dict[k] == '<REMOVED>':
                raise Exception(f'\n\tThe setting {key_path} has been removed. Please remove it from your settings file. See https://obsidian-html.github.io/Log/<fillin> for more information.')            
            raise Exception(f'\n\tThe value of key "{key_path}" is expected to be of type {type(base_dict[k])}, but is of type {type(v)}. {helptext}')

        # dict match -> recurse
        if isinstance(base_dict[k], dict) and isinstance(v, dict):
            base_dict[k] = MergeDictRecurse(base_dict[k], update_dict[k], path=key_path)
            continue
        
        # other cases -> copy over
        if isinstance(update_dict[k], list):
            base_dict[k] = v.copy()
        else:
            if base_dict[k] == '<REMOVED>':
                raise Exception(f'\n\tThe setting {key_path} has been removed. Please remove it from your settings file. See https://obsidian-html.github.io/Log/<fillin> for more information.')
            base_dict[k] = v

    return base_dict.copy()

def CheckConfigRecurse(config, path='', match_str='<REQUIRED_INPUT>'):
    helptext = '\n\nTip: Run obsidianhtml -gc to see all configurable keys and their default values.\n'

    for k, v in config.items():
        key_path = '/'.join(x for x in (path, k) if x !='')
        
        if isinstance(v, dict):
            CheckConfigRecurse(config[k], path=key_path)

        if v == match_str:
            raise Exception(f'\n\tKey "{key_path}" is required. {helptext}')

 