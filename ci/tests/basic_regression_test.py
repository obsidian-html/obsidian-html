from pathlib import Path
import shutil
import os
import sys
import yaml
import subprocess
import time

# web stuff
from bs4 import BeautifulSoup
import requests

# Defer tools
from contextlib import ExitStack
from functools import partial

# unittest
import unittest

# Helper functions
# --------------------------------
def get_paths():
    paths = {}
    this_file_path              = os.path.realpath(__file__)                           # (..)/obsidian-html/ci/tests/__filename__
    paths['ci_tests']           = Path(this_file_path).parent                          # (..)/obsidian-html/ci/tests/
    paths['root']               = paths['ci_tests'].parent.parent                      # (..)/obsidian-html/
    paths['ci_configs']         = paths['root'].joinpath('ci/configs')                 # (..)/obsidian-html/ci/configs
    paths['test_vault']         = paths['root'].joinpath('ci/test_vault')              # (..)/obsidian-html/ci/configs
    paths['temp_dir']           = paths['root'].joinpath('tmp')                        # (..)/obsidian-html/tmp
    paths['html_output_folder'] = paths['temp_dir'].joinpath('html')                   # (..)/obsidian-html/tmp/html
    #paths['config_yaml']        = paths['ci_configs'].joinpath('default_settings.yml') # (..)/obsidian-html/ci/configs/default_settings.yml
     
    return paths

def get_config(config_file_name):
    paths = get_paths()
    config_file_path = paths['ci_configs'].joinpath(config_file_name)
    with open(config_file_path, 'r', encoding="utf-8") as f:
        config = yaml.safe_load(f.read())

    return config

def convert_vault(config_file_name):
    # Get paths
    paths = get_paths()
    config_file_path = paths['ci_configs'].joinpath(config_file_name)
    
    # Get config yaml
    config = get_config(config_file_name)

    # Move to root folder and output paths
    os.chdir(paths['root'])

    # Convert files
    print(f"OBSIDIAN-HTML: converting ci/test_vault ({config_file_name})")
    subprocess.call(['python', '-m', 'obsidianhtml', '-i', config_file_path.as_posix()], stdout=subprocess.DEVNULL)    

def cleanup_temp_dir():
    #time.sleep(30)
    paths = get_paths()
    os.chdir(paths['root'])
    print(f"CLEANING TEMP DIR: {paths['temp_dir']}")
    if paths['temp_dir'] != '' and paths['temp_dir'] is not None and paths['temp_dir'] != '/':
        shutil.rmtree(paths['temp_dir'])
        print ('CLEANING TEMP DIR: done')

def html_get(path, output_dict=False):
    if path[0] == '/':
        path = path[1:]
    url = f"http://localhost:8888/{path}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, features="html5lib")

    if output_dict:
        return {'soup': soup, 'url': url}
    else:
        return soup



# Template
# -------------------------------
class ModeTemplate(unittest.TestCase):
    testcase_name = "Template"
    testcase_config = None      # contains the config.yml contents in dict form

    @classmethod
    def setUpClass(cls):
        cls.testcase_config = get_config(cls.testcase_config_file_name)
        convert_vault(cls.testcase_config_file_name)

    @classmethod
    def tearDownClass(cls):
        print()
        cleanup_temp_dir()

    def setUp(self):
        print()

    def scribe(self, msg):
        print(f'{self.testcase_name}:\t > {msg}')

    def assertPageFound(self, soup, msg=None):
        self.assertFalse('Error code explanation: HTTPStatus.NOT_FOUND - Nothing matches the given URI.' in soup.text, msg=msg)

    def self_check(self):
        self.scribe('(self check) config dict should have been fetched')
        config = self.testcase_config
        self.assertIn('site_name', config.keys())
    
    # Standard tests
    # -------------------------------
    def index_html_should_exist(self, path='index.html'):
        self.scribe('index.html should exist in the expected path')

        # Get index.html
        res = html_get(path, output_dict=True)
        self.assertPageFound(res['soup'], msg=f'expected page "{res["url"]}" was not found.')

        # Test content of index.html
        header_text = res['soup'].body.find('div', attrs={'class':'container'}).find('h1').text
        self.assertEqual(header_text, 'entrypoint', msg="Link expected in index.html with innerHtml of 'entrypoint'.")

        # Return note linked by obsidian link
        return res['soup'].body.find('a', text="Note link")['href']

    def obsidian_type_links_should_work(self, path):
        self.scribe('obsidian-type link should work')
        soup = html_get(path)
        self.assertPageFound(soup)

        # Return note linked by markdown link
        return soup.body.find('a', text="Markdownlink")['href']

    def markdown_type_links_should_work(self, path):
        self.scribe('markdown-type link should work')
        soup = html_get(path)
        self.assertPageFound(soup)

# Modes
# -------------------------------
class TestDefaultMode(ModeTemplate):
    """Use default settings and run all tests"""
    testcase_name = "Default"
    testcase_config_file_name = 'default_settings.yml'

    def test_A__test_self(self):
        "Tests working of the test structure"
        self.self_check()

    def test_B__index_and_links(self):
        "Tests placement of files and working of links"
        next_url = self.index_html_should_exist(path='index.html')
        next_url = self.obsidian_type_links_should_work(next_url)
        self.markdown_type_links_should_work(next_url)

class TestMisc(ModeTemplate):
    """Use default settings and run all tests"""
    testcase_name = "Default"
    testcase_config_file_name = 'process_all.yml'

    def test_special_characters_should_be_preserved(self):
        self.scribe('special characters should be preserved')
        soup = html_get('Special Characters.html')
        self.assertEqual(len(soup.text), 20915)


if __name__ == '__main__':
    # Args
    run_setup = False
    run_cleanup = False
    for i, v in enumerate(sys.argv):
        if v == '-r':
            run_setup = True
        if v == '-c':
            run_cleanup = True

    # get paths
    paths = get_paths()
    
    # Create temp dir
    os.chdir(paths['root'])
    paths['temp_dir'].mkdir(exist_ok=True)

    # Start webserver
    # ----------------------------
    # defer context for webserver
    with ExitStack() as stack:
        webserver_process = subprocess.Popen(['python', '-m', 'http.server', '--directory', paths['html_output_folder'], '8888'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # close server *always* on exit
        stack.callback(partial(webserver_process.terminate))
        stack.callback(partial(print, 'DEFERRED: closed webserver'))

        time.sleep(0.1)
        print("WEBSERVER: started on http://localhost:8888")

        # Run tests
        # ----------------------------
        unittest.main(failfast=True)

