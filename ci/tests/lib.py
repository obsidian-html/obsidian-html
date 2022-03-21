import os
import sys
import subprocess
import yaml
import shutil

# web stuff
from bs4 import BeautifulSoup
import requests
import html

from pathlib import Path

def get_paths():
    paths = {}
    this_file_path              = os.path.realpath(__file__)                                        # (..)/obsidian-html/ci/tests/__filename__
    paths['ci_tests']           = Path(this_file_path).parent                                       # (..)/obsidian-html/ci/tests/
    paths['root']               = paths['ci_tests'].parent.parent                                   # (..)/obsidian-html/
    paths['ci_src']             = paths['root'].joinpath('ci/src').resolve()                        # (..)/obsidian-html/ci/src/
    paths['sys_default_config'] = paths['root'].joinpath('obsidianhtml/src/defaults_config.yml')    # (..)/obsidian-html/obsidianhtml/src/defaults_config.yml
    paths['ci_configs']         = paths['root'].joinpath('ci/configs')                              # (..)/obsidian-html/ci/configs
    paths['test_vault']         = paths['root'].joinpath('ci/test_vault')                           # (..)/obsidian-html/ci/configs
    paths['temp_dir']           = paths['root'].joinpath('tmp')                                     # (..)/obsidian-html/tmp
    paths['temp_cfg']           = paths['temp_dir'].joinpath('config.yml')                          # (..)/obsidian-html/tmp/config.yml
    paths['html_output_folder'] = paths['temp_dir'].joinpath('html')                                # (..)/obsidian-html/tmp/html
    paths['config_yaml']        = paths['ci_configs'].joinpath('default_settings.yml')              # (..)/obsidian-html/ci/configs/default_settings.yml
     
    return paths


def convert_vault():
    # Get paths
    paths = get_paths()
    config_file_path = paths['temp_cfg']    # set by customize_default_config

    # Move to root folder and output paths
    os.chdir(paths['root'])

    # Convert files
    print(f"OBSIDIAN-HTML: converting ci/test_vault ({config_file_path.as_posix()})")
    subprocess.call(['python', '-m', 'obsidianhtml', '-i', config_file_path.as_posix()])#, stdout=subprocess.DEVNULL)    

def cleanup_temp_dir():
    #time.sleep(30)
    paths = get_paths()
    os.chdir(paths['root'])
    print(f"CLEANING TEMP DIR: {paths['temp_dir']}")
    if paths['temp_dir'] != '' and paths['temp_dir'] is not None and paths['temp_dir'] != '/':
        shutil.rmtree(paths['temp_dir'])
        print ('CLEANING TEMP DIR: done')

def requests_get(path):
    if path[0] == '/':
        path = path[1:]
    url = f"http://localhost:8888/{path}"
    return (requests.get(url), url)

def html_get(path, output_dict=False, convert=False):
    response, url = requests_get(path)

    if convert == False:
        soup = BeautifulSoup(response.text, features="html5lib")
    else:
        soup = BeautifulSoup(response.text, 'html.parser', features="html5lib")

    if output_dict:
        return {'soup': soup, 'url': url}
    else:
        return soup

def get_default_config():
    paths = get_paths()

    # Get functions from package
    sys.path.insert(1, str(paths['root']))   # insert at 1, 0 is the script path (or '' in REPL)
    from obsidianhtml.ConfigManager import CheckConfigRecurse, MergeDictRecurse     

    # Get system's default config
    with open(paths['sys_default_config'], 'r', encoding="utf-8") as f:
        sys_config = yaml.safe_load(f.read())

    # Get our default overwrites
    with open(paths['config_yaml'], 'r', encoding="utf-8") as f:
        default_config = yaml.safe_load(f.read())

    # Merge the two
    config = MergeDictRecurse(sys_config, default_config)

    return config

def customize_default_config(items, write_to_tmp_config=True):
    # Example Input
    # items = [
    #     ('toggles/features/create_index_from_tags/enabled', True),
    #     ('html_url_prefix', '/a'),
    #     ('toggles/process_all', True)
    # ]     

    paths = get_paths()

    # Get functions from package
    sys.path.insert(1, str(paths['root']))   # insert at 1, 0 is the script path (or '' in REPL)
    from obsidianhtml.ConfigManager import CheckConfigRecurse, MergeDictRecurse

    # Convert list to dict tree
    custom = {}
    for item in items:
        keys = item[0].split('/')
        value = item[1]

        _d = custom
        for i, k in enumerate(keys):
            if i == (len(keys) - 1):
                _d[k] = value
            else:
                if k not in _d:
                    _d[k] = {}
                _d = _d[k]

    # Merge with defaults
    base = get_default_config()
    output = MergeDictRecurse(base, custom)

    # Write output to file
    if write_to_tmp_config:
        paths['temp_cfg'].parent.mkdir(exist_ok=True)
        with open(paths['temp_cfg'], 'w', encoding="utf-8") as f:
            f.write(yaml.dump(output))

    # return dict to calling function
    return output

def exclude_str(exclude_list, string):
    for item in exclude_list:
        if item in string:
            return False
    return True