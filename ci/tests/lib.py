import os
import sys
import subprocess
import yaml
import shutil
import time
import unittest

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
    paths['test_vault']         = paths['root'].joinpath('ci/test_vault')                           # (..)/obsidian-html/ci/test_vault
    paths['temp_dir']           = paths['root'].joinpath('tmp')                                     # (..)/obsidian-html/tmp
    paths['temp_cfg']           = paths['temp_dir'].joinpath('config.yml')                          # (..)/obsidian-html/tmp/config.yml
    paths['html_output_folder'] = paths['temp_dir'].joinpath('html')                                # (..)/obsidian-html/tmp/html
    paths['config_yaml']        = paths['ci_configs'].joinpath('default_settings.yml')              # (..)/obsidian-html/ci/configs/default_settings.yml
    paths['unit_config_yaml']   = paths['ci_configs'].joinpath('unit_test_settings.yml')            # (..)/obsidian-html/ci/configs/unit_test_settings.yml
    paths['test_entrypoint']    = paths['test_vault'].joinpath('entrypoint.md')                     # (..)/obsidian-html/ci/test_vault/entrypoint.md

    paths['unit_test_input_output_folder']    = paths['root'].joinpath('ci/unit_tests/input_output')    # (..)/obsidian-html/ci/unit_tests/input_output
     
    return paths


def convert_vault(USE_PIP_INSTALL):

    # Get paths
    paths = get_paths()
    config_file_path = paths['temp_cfg']    # set by customize_default_config

    # Move to root folder and output paths
    os.chdir(paths['root'])

    # Convert files
    print(f"OBSIDIAN-HTML: converting ci/test_vault ({config_file_path.as_posix()})")
    if USE_PIP_INSTALL:
        subprocess.call(['obsidianhtml', 'convert', '-i', config_file_path.as_posix()])#, stdout=subprocess.DEVNULL)    
    else:
        subprocess.call(['python', '-m', 'obsidianhtml', 'convert', '-i', config_file_path.as_posix()])#, stdout=subprocess.DEVNULL)    

def cleanup_temp_dir():
    paths = get_paths()
    os.chdir(paths['root'])
    print(f"CLEANING TEMP DIR: {paths['temp_dir']}")
    if paths['temp_dir'] != '' and paths['temp_dir'] is not None and paths['temp_dir'] != '/':
        shutil.rmtree(paths['temp_dir'])
        print ('CLEANING TEMP DIR: done')

def requests_get(path):
    if path[0] == '/':
        path = path[1:]
    url = f"http://localhost:8088/{path}"
    return (requests.get(url), url)

def html_get(path, output_dict=False, convert=False):
    response, url = requests_get(path)

    if convert == False:
        soup = BeautifulSoup(response.text, features="html5lib")
    else:
        soup = BeautifulSoup(response.text, 'html.parser', features="html5lib")

    if output_dict:
        return {'soup': soup, 'url': url, 'text': response.text}
    else:
        return soup

def get_default_config():
    paths = get_paths()

    # Get functions from package
    sys.path.insert(1, str(paths['root']))   # insert at 1, 0 is the script path (or '' in REPL)
    from obsidianhtml.lib import MergeDictRecurse

    # Get system's default config
    with open(paths['sys_default_config'], 'r', encoding="utf-8") as f:
        sys_config = yaml.safe_load(f.read())

    # Get our default overwrites
    with open(paths['config_yaml'], 'r', encoding="utf-8") as f:
        default_config = yaml.safe_load(f.read())

    # Merge the two
    config = MergeDictRecurse(sys_config, default_config)

    # Clean out removed keys
    def rec(d):
        if isinstance(d, list):
            for item in d:
                rec(item)
        if isinstance(d, dict):
            finished = False
            while finished == False:
                finished = True
                for key in d.keys():
                    if isinstance(d[key], str) and d[key] == '<REMOVED>':
                        d.pop(key)
                        finished = False
                        break
                    else:
                        rec(d[key])
    rec(config)

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
    from obsidianhtml.lib import MergeDictRecurse

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

    # Clean out deprecated keys
    def rec(d):
        if isinstance(d, list):
            for item in d:
                rec(item)
        if isinstance(d, dict):
            finished = False
            while finished == False:
                finished = True
                for key in d.keys():
                    if isinstance(d[key], str) and d[key] in ['<DEPRECATED>']:
                        d.pop(key)
                        finished = False
                        break
                    else:
                        rec(d[key])
    rec(output)

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

def GetRssSoup(file_path):
    full_path = Path('tmp/html/').joinpath(file_path).resolve()
    with open(full_path, 'r', encoding="utf-8") as f:
        rss = f.read()
    soup = BeautifulSoup(rss, 'lxml')

    articles = soup.findAll('item')
    articles_dicts = [{'title':a.find('title').text,'link':a.link.next_sibling.replace('\n','').replace('\t',''),'description':a.find('description').text,'pubdate':a.find('pubdate').text} for a in articles]
    urls = [d['link'] for d in articles_dicts if 'link' in d]
    titles = [d['title'] for d in articles_dicts if 'title' in d]
    descriptions = [d['description'] for d in articles_dicts if 'description' in d]
    pub_dates = [d['pubdate'] for d in articles_dicts if 'pubdate' in d]

    return {
        'articles': articles_dicts,
        'urls': urls,
        'titles': titles,
        'descriptions': descriptions,
        'pub_dates': pub_dates
    }

class ModeTemplate(unittest.TestCase):
    testcase_name = "Template"
    testcase_config = None                  # contains the config dict
    testcase_custom_config_values = []      # can contain overrides for the default config
    tear_down = True
    USE_PIP_INSTALL = (os.getenv('OBS_HTML_USE_PIP_INSTALL') == 'true')

    @classmethod
    def setUpClass(cls):
        print(f'\n\n--------------------- {cls.testcase_name} -----------------------------', flush=True)
        cls.testcase_config = customize_default_config(cls.testcase_custom_config_values)
        convert_vault(cls.USE_PIP_INSTALL)

    @classmethod
    def tearDownClass(cls):
        print('\n\ntear_down', cls.tear_down)
        if cls.tear_down:
            print('', flush=True)
            cleanup_temp_dir()

    def setUp(self):
        print('', flush=True)

    def scribe(self, msg):
        print(f'{self.testcase_name}:\t > {msg}', flush=True)

    def assertPageFound(self, soup, msg=None):
        self.assertFalse('Nothing matches the given URI.' in soup.text, msg=msg)

    def assertPageNotFound(self, soup, msg=None):
        self.assertTrue('Nothing matches the given URI.' in soup.text, msg=msg)

    def self_check(self):
        self.scribe('(self check) config dict should have been fetched')
        config = self.testcase_config
        self.assertIn('obsidian_entrypoint_path_str', config.keys())
    
    # Standard tests
    # -------------------------------
    def index_html_should_exist(self, path='index.html'):
        self.scribe('index.html should exist in the expected path')

        # Get index.html
        res = html_get(path, output_dict=True)
        self.assertPageFound(res['soup'], msg=f'expected page "{res["url"]}" was not found.')

        # Test content of index.html
        header_text = res['soup'].body.find('div', attrs={'class':'container'}).find('h1').text
        self.assertEqual(header_text, 'entrypoint', msg="H1 expected in index.html with innerHtml of 'entrypoint'.")

        # Return note linked by obsidian link
        link_text = 'Note link'
        a = res['soup'].body.find('a', string=link_text)
        self.assertIsNotNone(a, msg=f"Note link with text '{link_text}' is not found in index.html")
        return a['href']

    # deprecated for links_should_work()
    def obsidian_type_links_should_work(self, path, link_text='Markdownlink'):
        self.scribe('obsidian-type link should work')
        soup = html_get(path)
        self.assertPageFound(soup, msg=f'expected page "{path}" was not found.')

        # Return note linked by markdown link
        a = soup.body.find('a', string=link_text)
        self.assertIsNotNone(a, msg=f"Markdown link with text '{link_text}' is not found in index.html")
        return a['href']

    # deprecated for links_should_work()
    def markdown_type_links_should_work(self, path):
        self.scribe('markdown-type link should work')
        soup = html_get(path)
        self.assertPageFound(soup, msg=f'expected page "{path}" was not found.')

    def links_should_work(self, path, link_type_tested="unknown", link_text='Markdownlink', mode=None):
        self.scribe(f'links of type {link_type_tested} should work')
        
        # Get origin page
        soup = html_get(path)
        self.assertPageFound(soup, msg=f'expected page "{path}" was not found.')

        # Get url from the a href with the link text
        a = soup.body.find('a', string=link_text)
        self.assertIsNotNone(a, msg=f"Link of type {link_type_tested} with text '{link_text}' is not found on {path}")

        # Test link
        soup = html_get(a['href'])

        if mode is None:
            self.assertPageFound(soup, msg=f'expected page "{a["href"]}" was not found.')
        elif mode == 'ShouldNotExist':
            self.assertPageNotFound(soup, msg=f"Page found when note should not have been included. URL: {a['href']}")

        return a['href']

def check_md_output(folder, expected_files):
    paths = get_paths()
    actual_files = os.listdir(f"{paths['temp_dir']}/{folder}")

    issues = []
    
    # test files exist that shouldn't
    for file in actual_files:
        if file not in expected_files:
            issues.append(f"File {file} exists but it should not.")

    # test files that should exist but don't
    for file in expected_files:
        if file not in actual_files:
            issues.append(f"File {file} should exist but it does not.")

    return (issues, actual_files)