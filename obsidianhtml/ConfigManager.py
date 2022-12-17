import sys
import json
import yaml
import inspect

from functools import cache
from pathlib import Path 

from . import print_global_help_and_exit
from .lib import OpenIncludedFile, FindVaultByEntrypoint, get_default_appdir_config_yaml_path
from .v4 import Types as T

class Config:
    config = None
    pb = None

    def __init__(self, pb, input_yml_path_str=False):
        '''
        This init function will do three steps:
        - Merging default config with user config
        - Check that all required values are filled in, all user provided settings are known in default config
        - Setting missing values / Checking for illegal configuration
        '''
        self.pb = pb

        # merge
        user_config    = self.load_user_config(input_yml_path_str)
        default_config = yaml.safe_load(OpenIncludedFile('defaults_config.yml'))
        self.config    = MergeDictRecurse(default_config, user_config)

        # check settings / set missing values / overwriting values
        self.check_required_values_filled_in(self.config)
        self.resolve_deprecations(default_config, user_config)              # Temporary patches during deprecation
        self.overwrite_values()
        self.check_entrypoint_exists()                                      # A value for the entrypoint is required, as this will become the index
        self.set_obsidian_folder_path_str()                                 # Determine obsidian folder path based on either the user telling us, or from the entrypoint
        self.load_capabilities_needed()                                     # Capabilities are "summary toggles" that can tell us at a glance whether we should enable something or not.

        # Plugins
        self.plugin_settings = {}

    def load_user_config(self, input_yml_path_str=False) -> dict:
        ''' 
            Will load the config.yml as provided by the user, and convert it to a python dict, which is returned. 
            Any error in this process will be terminating. 
            Auto loading a config yaml based on default locations should be done elsewhere. The determined path can then be filled in in input_yml_path_str.
        '''
        
        # Make sure the user passes in a config file
        if input_yml_path_str == False:
            print('ERROR: No config file passed in. Use -i <path/to/config.yml> to pass in a config yaml.')
            print_global_help_and_exit(1)

        # Load input yaml
        try:
            with open(input_yml_path_str, 'rb') as f:
                input_config =yaml.safe_load(f.read())
        except FileNotFoundError:
            print(f'Could not locate the config file {input_yml_path_str}.\n  Please try passing the exact location of it with the `obsidianhtml -i /your/path/to/{input_yml_path_str}` parameter.')
            print_global_help_and_exit(1)

        # Return
        return input_config

    def resolve_deprecations(self, base_dict, update_dict):
        # if exclude_subfolders is present, copy it to exclude_glob
        if 'exclude_subfolders' in update_dict.keys() and isinstance(update_dict['exclude_subfolders'], list):
            self.config['exclude_glob'] = self.config['exclude_subfolders']

    def overwrite_values(self):
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

    def check_entrypoint_exists(self):
        if self.config['toggles']['compile_md'] == False:       # don't check vault if we are compiling directly from markdown to html
            return
        if not Path(self.config['obsidian_entrypoint_path_str']).exists():
            print(f"Error: entrypoint note {self.config['obsidian_entrypoint_path_str']} does not exist.")
            exit(1)

    def set_obsidian_folder_path_str(self):
        if self.config['toggles']['compile_md'] == False:       # don't check vault if we are compiling directly from markdown to html
            return

        # Use user provided obsidian_folder_path_str
        if 'obsidian_folder_path_str' in self.config and self.config['obsidian_folder_path_str'] != '<DEPRECATED>':
            result = FindVaultByEntrypoint(self.config['obsidian_folder_path_str'])
            if result:
                if Path(result) != Path(self.config['obsidian_folder_path_str']).resolve():
                    print(f"Error: The configured obsidian_folder_path_str is not the vault root. Change its value to {result}" )
                    exit(1)
                return
            else:
                print(f"ERROR: Obsidianhtml could not find a valid vault. (Tip: obsidianhtml looks for the .obsidian folder)")
                exit(1)
            return

        # Determine obsidian_folder_path_str from obsidian_entrypoint_path_str
        result = FindVaultByEntrypoint(self.config['obsidian_entrypoint_path_str'])
        if result:
            self.config['obsidian_folder_path_str'] = result
            if self.pb.verbose:
                print(f"Set obsidian_folder_path_str to {result}")
        else:
            print(f"ERROR: Obsidian vault not found based on entrypoint {self.config['obsidian_entrypoint_path_str']}.\n\tDid you provide a note that is in a valid vault? (Tip: obsidianhtml looks for the .obsidian folder)")
            exit(1)

    def load_capabilities_needed(self):
        self.capabilities_needed = {}
        gc = self.get_config

        self.capabilities_needed['directory_tree'] = False 
        if gc('toggles/features/styling/add_dir_list') or gc('toggles/features/create_index_from_dir_structure/enabled'):
            self.capabilities_needed['directory_tree'] = True

        self.capabilities_needed['search_data'] = False
        if gc('toggles/features/search/enabled') or gc('toggles/features/graph/enabled') or gc('toggles/features/embedded_search/enabled'):
            self.capabilities_needed['search_data'] = True

        self.capabilities_needed['graph_data'] = False
        if gc('toggles/features/rss/enabled') or gc('toggles/features/graph/enabled'):
            self.capabilities_needed['graph_data'] = True

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
        keys = [x for x in path.strip().split('/') if x != '']

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
    def ShowIcon(self, feature_name):
        return (self.pb.gc(f'toggles/features/{feature_name}/enabled') and self.pb.gc(f'toggles/features/{feature_name}/styling/show_icon'))

    def LoadIncludedFiles(self):
        # Get html template code. 
        if self.pb.gc('toggles/compile_html', cached=True):
            # Every note will become a html page, where the body comes from the note's markdown, 
            # and the wrapper code from this template.
            try:
                with open(Path(self.pb.gc('html_template_path_str')).resolve()) as f:
                    html_template = f.read()
            except:
                layout = self.pb.gc('toggles/features/styling/layout')
                html_template = OpenIncludedFile(f'html/layouts/template_{layout}.html')

            if '{content}' not in html_template:
                raise Exception('The provided html template does not contain the string `{content}`. This will break its intended use as a template.')
                exit(1)

            self.pb.html_template = html_template

        
        if self.pb.gc('toggles/features/graph/enabled', cached=True):
            # Get graph template
            self.pb.graph_template = OpenIncludedFile('graph/graph_template.html')

            # Get graph full page template
            self.pb.graph_full_page_template = OpenIncludedFile('graph/graph_full_page.html')
            
            # Get grapher template code
            self.pb.graphers = []
            i = 0
            for grapher in self.pb.gc('toggles/features/graph/templates', cached=True):
                gid = grapher['id']

                # get contents of the file
                if grapher['path'].startswith('builtin<'):
                    grapher['contents'] = OpenIncludedFile(f'graph/default_grapher_{gid}.js')
                else:
                    try:
                        with open(Path(grapher['path']).resolve()) as f:
                            grapher['contents'] = f.read()
                    except:
                        raise Exception(f"Could not open user provided grapher file with path {temp_path}")
            
                self.pb.graphers.append(grapher)


    def LoadEmbeddedNoteConfig(self, data_json_path):
        self.plugin_settings['embedded_note_titles'] = {}
        if data_json_path.exists():
            with open(data_json_path, 'r', encoding='utf-8') as f:
                self.plugin_settings['embedded_note_titles'] = json.loads(f.read())
            return True
        return False

    def check_required_values_filled_in(self, config, path='', match_str='<REQUIRED_INPUT>'):
        def rec(config, path='', match_str='<REQUIRED_INPUT>'):
            helptext = '\n\nTip: Run obsidianhtml -gc to see all configurable keys and their default values.\n'

            for k, v in config.items():
                key_path = '/'.join(x for x in (path, k) if x !='')
                
                if isinstance(v, dict):
                    rec(config[k], path=key_path)

                if v == match_str:
                    raise Exception(f'\n\tKey "{key_path}" is required. {helptext}')
        rec(config, path, match_str)

def MergeDictRecurse(base_dict, update_dict, path=''):
    helptext = '\n\nTip: Run obsidianhtml -gc to see all configurable keys and their default values.\n'

    def check_leaf(key_path, val):
        if val == '<REMOVED>':
            raise Exception(f'\n\tThe setting {key_path} has been removed. Please remove it from your settings file. See https://obsidian-html.github.io/Configurations/Deprecated%20Configurations/Deprecated%20Configurations.html for more information.')
        elif val == '<DEPRECATED>':
            print(f'DEPRECATION WARNING: The setting {key_path} is deprecated. See https://obsidian-html.github.io/Configurations/Deprecated%20Configurations/Deprecated%20Configurations.html for more information.')
            return False
        return True

    for k, v in update_dict.items():
        key_path = '/'.join(x for x in (path, k) if x !='')

        # every configured key should be known in base config, otherwise this might suggest a typo/other error
        if k not in base_dict.keys():
            raise Exception(f'\n\tThe configured key "{key_path}" is unknown. Check for typos/indentation. {helptext}')

        # don't overwrite a dict in the base config with a string, or something else
        # in general, we don't expect types to change
        if type(base_dict[k]) != type(v):
            if check_leaf(key_path, base_dict[k]):
                raise Exception(f'\n\tThe value of key "{key_path}" is expected to be of type {type(base_dict[k])}, but is of type {type(v)}. {helptext}')

        # dict match -> recurse
        if isinstance(base_dict[k], dict) and isinstance(v, dict):
            base_dict[k] = MergeDictRecurse(base_dict[k], update_dict[k], path=key_path)
            continue
        
        # other cases -> copy over
        if isinstance(update_dict[k], list):
            base_dict[k] = v.copy()
        else:
            check_leaf(key_path, base_dict[k])
            base_dict[k] = v

    return base_dict.copy()


def find_user_config_yaml_path(config_yaml_location) -> T.OSAbsolutePosx:
    ''' This function finds the correct path to load the user config from. It has these options: user provided path (-i path/config.yml), default location, ... '''
    input_yml_path_str = ''

    # Use given value
    if config_yaml_location != '':
        input_yml_path_str = config_yaml_location
    else:
        input_yml_path_str = ''
        for i, v in enumerate(sys.argv):
            if v == '-i':
                if len(sys.argv) < (i + 2):
                    print(f'No config path given.\n  Use `obsidianhtml convert -i /target/path/to/config.yml` to provide input.')
                    #print_global_help_and_exit(1)
                    exit(1)
                input_yml_path_str = sys.argv[i+1]
                break

    # Try to find config in default locations
    if input_yml_path_str == '':
        # config.yml in same folder
        if Path('config.yml').exists():
            input_yml_path_str = Path('config.yml').resolve().as_posix()
            print(f"No config provided, using config at {input_yml_path_str} (Default config path)")
    if input_yml_path_str == '':
        # config.yaml in same folder
        if Path('config.yaml').exists():
            input_yml_path_str = Path('config.yaml').resolve().as_posix()
            print(f"No config provided, using config at {input_yml_path_str} (Default config path)")
    if input_yml_path_str == '':
        # config.yml in appdir folder
        appdir_config = Path(get_default_appdir_config_yaml_path())
        if appdir_config.exists():
            input_yml_path_str = appdir_config.as_posix()
            print(f"No config provided, using config at {input_yml_path_str} (Default config path)")

    if input_yml_path_str == '':
        print(f'No config path given, and none found in default locations.\n  Use `obsidianhtml convert -i /target/path/to/config.yml` to provide input.')
        exit(1)

    return input_yml_path_str
