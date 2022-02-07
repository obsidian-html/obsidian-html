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
def html_get(path):
    if path[0] == '/':
        path = path[1:]
    response = requests.get(f"http://localhost:8888/{path}")

    return BeautifulSoup(response.text, features="html5lib")

def get_paths():
    paths = {}
    this_file_path              = os.path.realpath(__file__)                           # (..)/obsidian-html/ci/tests/__filename__
    paths['ci_tests']           = Path(this_file_path).parent                          # (..)/obsidian-html/ci/tests/
    paths['root']               = paths['ci_tests'].parent.parent                      # (..)/obsidian-html/
    paths['ci_configs']         = paths['root'].joinpath('ci/configs')                 # (..)/obsidian-html/ci/configs
    paths['test_vault']         = paths['root'].joinpath('ci/test_vault')              # (..)/obsidian-html/ci/configs
    paths['temp_dir']           = paths['root'].joinpath('tmp')                        # (..)/obsidian-html/tmp
    paths['html_output_folder'] = paths['temp_dir'].joinpath('html')                   # (..)/obsidian-html/tmp/html
    paths['config_yaml']        = paths['ci_configs'].joinpath('default_settings.yml') # (..)/obsidian-html/ci/configs/default_settings.yml
     
    return paths

   

# Testclasses
# -------------------------------
class TestDefaultSettings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Get paths
        paths = get_paths()
        
        # Get default config.yaml
        with open(paths['config_yaml'], 'r', encoding="utf-8") as f:
            config = yaml.safe_load(f.read())

        # Move to root folder and output paths
        os.chdir(paths['root'])

        # Convert files
        print("OBSIDIAN-HTML: converting ci/test_vault")
        subprocess.call(['python', '-m', 'obsidianhtml', '-i', paths['config_yaml'].as_posix()], stdout=subprocess.DEVNULL)

    @classmethod
    def tearDownClass(cls):
        paths = get_paths()
        os.chdir(paths['root'])
        print(f"CLEANING TEMP DIR: {paths['temp_dir']}")
        if paths['temp_dir'] != '' and paths['temp_dir'] is not None and paths['temp_dir'] != '/':
            shutil.rmtree(paths['temp_dir'])
            print ('CLEANING TEMP DIR: done') 

    def assertPageFound(self, soup):
        self.assertFalse('Error code explanation: HTTPStatus.NOT_FOUND - Nothing matches the given URI.' in soup.text)

    def test_file_access_and_links(self):
        # Get index.html
        soup = html_get('index.html')
        self.assertPageFound(soup)
    
        # Test content of index.html
        header_text = soup.body.find('div', attrs={'class':'container'}).find('h1').text
        self.assertEqual(header_text, 'entrypoint')

        # Test that obsidian type links are processed correctly by fetching next note
        soup = html_get(soup.body.find('a', text="Note link")['href'])
        self.assertPageFound(soup)

        # Test that markdown type links are processed correctly by fetching next note
        soup = html_get(soup.body.find('a', text="Markdownlink")['href'])
        self.assertPageFound(soup)


if __name__ == '__main__':
    print()

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

    # Clean up
    # --------------------------------

