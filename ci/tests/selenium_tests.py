from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options

from pathlib import Path
import yaml

import time
import os
import sys
import subprocess

# Defer tools
from contextlib import ExitStack
from functools import partial

# add /obsidian-html/ci to path
sys.path.insert(1, str(Path(os.path.realpath(__file__)).parent.parent))
from tests.lib import *    


if __name__ == "__main__":
    paths = get_paths()

    # add ci/src to path so that we can load the gecko driver
    os.environ["PATH"] = paths['ci_src'].as_posix() + ':' + os.environ["PATH"]

    # Create temp dir
    os.chdir(paths['root'])
    paths['temp_dir'].mkdir(exist_ok=True)


    # Create context to start webserver in so that it always closes, even on error
    with ExitStack() as stack:
        webserver_process = subprocess.Popen(['python', '-m', 'http.server', '--directory', paths['html_output_folder'], '8888'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # close server *always* on exit
        stack.callback(partial(webserver_process.terminate))
        stack.callback(partial(print, 'DEFERRED: closed webserver'))

        # small wait because the webserver takes a little bit before it is running
        time.sleep(0.1)
        print(f"WEBSERVER: started on http://localhost:8888 in {paths['html_output_folder']}")

        # Compile output
        customize_default_config([])
        convert_vault()

        # Start selenium
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options=options)
        stack.callback(partial(driver.quit))

        # Tests
        driver.get("http://localhost:8888/")
        level = 0
        loop = True
        while loop:
            container = driver.find_element(by=By.ID, value=f'level-{level}')
            h1 = container.find_element(by=By.TAG_NAME, value='h1')
            print(h1.text)
            links = container.find_elements(by=By.TAG_NAME, value='a')

            loop = False
            for link in links:
                if exclude_str(['anchor','backlink'], link.get_attribute('class')):
                    loop = True
                    link.click()
                    time.sleep(0.1)
                    break
            level += 1