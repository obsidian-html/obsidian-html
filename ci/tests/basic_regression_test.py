#!/usr/bin/env python

from pathlib import Path
import os
import sys
import yaml
import subprocess
import time
import shutil

# web stuff
from bs4 import BeautifulSoup
import requests
import html

# Defer tools
from contextlib import ExitStack
from functools import partial

# unittest
import unittest
 
# Helper functions
# --------------------------------
# add /obsidian-html/ci to path
sys.path.insert(1, str(Path(os.path.realpath(__file__)).parent.parent))
from tests.lib import *

USE_PIP_INSTALL = (os.getenv('OBS_HTML_USE_PIP_INSTALL') == 'true')


# Modes
# -------------------------------
class TestDefaultMode(ModeTemplate):
    """Use default settings and run all tests"""
    testcase_name = "Default"
    testcase_custom_config_values = [
        ('toggles/features/rss/enabled', True)
    ]  
    tear_down = False

    def test_A__test_self(self):
        "Tests working of the test structure"
        self.self_check()

    def test_B__index_and_links(self):
        "Tests placement of files and working of links"
        next_url = self.index_html_should_exist(path='index.html')
        next_url = self.obsidian_type_links_should_work(next_url)
        self.markdown_type_links_should_work(next_url)

    def test_C_rss(self):
        self.scribe('rss should exist and the values should be filled in correctly.')

        rss = GetRssSoup('obs.html/rss/feed.xml')
        
        # test setting title, description, pubdate with frontmatter yaml
        item1 = [x for x in rss['articles'] if x['link'].strip() == "https://localhost:8088/rss/rss_index.html"][0]
        self.assertEqual(item1['title'], 'test_value_title')
        self.assertEqual(item1['description'], 'test_value_description')
        self.assertTrue(item1['pubdate'].startswith('Wed, 10 Dec 1980 00:00:00'))

        # test h1 fallback
        item2 = [x for x in rss['articles'] if x['link'].strip() == "https://localhost:8088/rss/rss_h1.html"][0]
        self.assertEqual(item2['title'], 'rss_h1_test')

        # test folder exclusion
        self.assertTrue(len([x for x in rss['articles'] if x['link'].strip() == "https://localhost:8088/rss_exclude1.html"]) == 0)

    def test_D_images(self):
        self.scribe('image link should point to correct location and the image should be downloadable.')

        img_rel_url = '/images/obsidian-html-logo.png'
        img_note_rel_url = '/Images.html'

        # Get image link
        soup = html_get(img_note_rel_url)
        img = soup.body.find('div', attrs={'class':'container'}).find('img')
        self.assertEqual(img['src'], img_rel_url)

        # Get image
        r = requests.get(f'http://localhost:8088{img_rel_url}')
        self.assertEqual(len(r.content), 10134)


    def test_F_note_inclusion_rel_link_depth(self):
        self.scribe("links in included notes should reflect caller's page depth")
        soup = html_get('note_inclusion/noteA.html')
        self.assertPageFound(soup)

        self.assertIsNotNone(soup.find('a', attrs={'id':'dirtree_link'}))
        
        img_url = "/images/obsidian-html-logo.png"
        imgs = soup.body.find('div', attrs={'class':'container'}).find_all('img')
        img_urls = [x['src'] for x in imgs]
        self.assertEqual(img_url, img_urls[0], msg="image url should be correct")
        self.assertEqual(len(img_urls), 2, msg="only two images should have been found")
        self.assertEqual(img_urls[1], img_urls[0], msg="both images should have the same url")
        
        note_url = "/note_inclusion/level1/level2/noteC.html"
        notes = soup.body.find('div', attrs={'class':'container'}).find_all('a', attrs={'class': None})
        note_urls = [x['href'] for x in notes]
        self.assertEqual(note_url, note_urls[0], msg="note url should be correct")
        self.assertEqual(len(note_urls), 2, msg="only two notelinks should have been found")
        self.assertEqual(note_urls[1], note_urls[0], msg="both note links should have the same url")

        video_url = "/video/mp4/reaction_Objection_birb.mp4"
        videos = soup.body.find('div', attrs={'class':'container'}).find_all('video')
        video_urls = [x.find('source')['src'] for x in videos]
        self.assertEqual(video_url, video_urls[0], msg="video url should be correct")
        self.assertEqual(len(video_urls), 2, msg="only two videolinks should have been found")
        self.assertEqual(video_urls[1], video_urls[0], msg="both video links should have the same url")
        

class TestDefaultModeMdOnly(TestDefaultMode):
    """Same as test default mode, but use md directly"""
    testcase_name = "MdOnly"
    testcase_custom_config_values = [
        ('toggles/features/rss/enabled', True), 
        ('toggles/compile_md', False), 
        ('obsidian_folder_path_str', 'DUMMY'), 
        ('obsidian_entrypoint_path_str', 'DUMMY'), 
    ]  
    tear_down = True

    @classmethod
    def setUpClass(cls):
        print(f'\n\n--------------------- {cls.testcase_name} <custom> -----------------------------', flush=True)

        print(f"removing {paths['html_output_folder']}")
        shutil.rmtree(paths['html_output_folder'])

        cls.testcase_config = customize_default_config(cls.testcase_custom_config_values)
        convert_vault(USE_PIP_INSTALL)


class TestHtmlPrefixMode(ModeTemplate):
    """Configure a HTML prefix"""
    testcase_name = "HtmlPrefix"
    testcase_custom_config_values = [
        ('html_url_prefix', '/a'),
        ('html_output_folder_path_str', 'tmp/html/a/'), 
        ('copy_vault_to_tempdir_method', 'shutil')
    ]


    def test_A__test_self(self):
        "Tests working of the test structure"
        self.self_check()

    def test_B__index_and_links(self):
        "Tests placement of files and working of links"
        next_url = self.index_html_should_exist(path=f'{self.testcase_config["html_url_prefix"][1:]}/index.html')
        next_url = self.obsidian_type_links_should_work(next_url)
        #self.markdown_type_links_should_work(next_url)

    def test_C_images(self):
        self.scribe('image link should point to correct location and the image should be downloadable.')

        img_rel_url = '/a/images/obsidian-html-logo.png'
        img_note_rel_url = '/a/Images.html'

        # Get image link
        soup = html_get(img_note_rel_url)
        img = soup.body.find('div', attrs={'class':'container'}).find('img')
        self.assertEqual(img['src'], img_rel_url)

        # Get image
        r = requests.get(f'http://localhost:8088{img_rel_url}')
        self.assertEqual(len(r.content), 10134)

class TestCreateIndexFromTagsMode(ModeTemplate):
    """Compile index from a list of tags"""
    testcase_name = "IndexFromTags"
    testcase_custom_config_values = [
        ('toggles/features/create_index_from_tags/enabled', True),
        ('toggles/features/create_index_from_tags/use_as_homepage', True),
        ('toggles/features/create_index_from_tags/tags', ['type/index1', 'type/index2'])
    ]  

    def index_html_should_exist(self, path='index.html'):
        self.scribe('index.html should exist in the expected path')

        # Get index.html
        res = html_get(path, output_dict=True)
        self.assertPageFound(res['soup'], msg=f'expected page "{res["url"]}" was not found.')

        # Test content of index.html
        header_text = res['soup'].body.find('div', attrs={'class':'container'}).find('h2').string
        self.assertEqual(header_text, 'type/index1', msg=f"H2 expected in index.html with innerHtml of 'type/index1'; was '{header_text}' instead.")        

        # Return note linked by obsidian link
        link_text = 'create_index_from_tags'
        a = res['soup'].body.find('a', string=link_text)
        self.assertIsNotNone(a, msg=f"Note link with text '{link_text}' is not found in index.html")
        return a['href']

    def test_A__test_self(self):
        "Tests working of the test structure"
        self.self_check()

    def test_B__index_and_links(self):
        "Tests placement of files and working of links"
        #time.sleep(100)
        next_url = self.index_html_should_exist(path='index.html')

        # Test auto-generated type links
        link_url = self.links_should_work(path='index.html', link_text='create_index_from_tags', link_type_tested="auto-generated")

        # Test Obsidian type links
        link_url = self.links_should_work(path=link_url, link_text='create_index_from_tags2', link_type_tested="Obsidian")
        
        # Test markdown type links
        link_url = self.links_should_work(path=link_url, link_text='create_index_from_tags3', link_type_tested="Markdown")

        # Test folder up
        link_url = self.links_should_work(path=link_url, link_text='create_index_from_tags4', link_type_tested="Obsidian")

        # This note should be included when process_all:False even though it does not match tags (default)
        link_url = self.links_should_work(path=link_url, link_text='create_index_from_tags5', link_type_tested='Obsidian')

        # This note should NOT be included when process_all:False (not linked to)
        res = html_get('modes/create_index_from_tags6.html', output_dict=True)
        self.assertPageNotFound(res['soup'], msg=f"Page found when note should not have been included. URL: {res['url']}")
    
class TestMisc(ModeTemplate):
    """Use process_all & copy_vault_to_tempdir: False"""
    testcase_name = "MiscTests"
    testcase_custom_config_values = [
        ('toggles/verbose_printout', True),
        ('toggles/process_all', True),
        ('html_template_path_str', 'ci/configs/custom_html_template.html'),
        ('copy_vault_to_tempdir', False),
        # disable all non essential features
        ('toggles/features/theme_picker/enabled', False),
        ('toggles/features/code_highlight/enabled', False),
        ('toggles/features/mermaid_diagrams/enabled', False),
        ('toggles/features/callouts/enabled', False),
        ('toggles/features/math_latex/enabled', False),
        ('toggles/features/backlinks/enabled', False),
        ('toggles/features/search/enabled', False),
        ('toggles/features/tags_page/enabled', False),
        ('toggles/features/dataview/enabled', False),
        ('toggles/features/graph/enabled', False),
        ('toggles/features/create_index_from_tags/enabled', False),
        ('toggles/features/rss/enabled', False),
        ('toggles/features/create_index_from_dir_structure/enabled', False),
    ]

    def test_special_characters_should_be_preserved(self):
        self.scribe('special characters should be preserved')

        response, url = requests_get('Special%20Characters.html')
        r = response.content.decode('utf-8')

        special_chars = 'wSBуghpзючKсшamь#ы7хTгLяfnмvеkrлоztFû9ёiъкищнтэ1́цRвйVO%бжs⟨фдп'
        for c in special_chars:
            self.assertIn(c, r, msg=f"character '{c}' expected but not found in 'Special Characters.html'.")

    def test_if_custom_template_is_used(self):
        self.scribe('custom html template should be used')
        
        # get index.html
        soup = html_get('index.html')

        # find div with certain ID from custom template, and doublecheck the contents to be sure.
        div_id = 'test'
        div = soup.body.find('div', attrs={'id':div_id})
        self.assertIsNotNone(div, msg=f"Div from custom template with id={div_id} was not found.")

        content = "See if this div is included"
        self.assertEqual(div.text, content, msg=f"innerhtml of custom div was expected to be \n\t'{content}'\n but was \n\t'{div.text}'")


class TestAFiltering1(ModeTemplate):
    testcase_name = "FilteringTests"
    testcase_custom_config_values = [
        ('obsidian_entrypoint_path_str', 'ci/test_vault/filtering/home.md'), 
        ('module_config/get_file_list/include_glob/value', ['filtering/**/*']),
        ('copy_vault_to_tempdir', False),
    ]
    def test_include_folder(self):
        self.scribe('Only include the included folder')
        issues, actual_files = check_md_output('md', ['not_created.md', 'filtering', 'index.md'])
        self.assertEqual(len(issues), 0, msg=f"Issues found with filtering\n{actual_files}\n{yaml.dump(issues)}")

class TestAFiltering2(ModeTemplate):
    testcase_name = "FilteringTests"
    testcase_custom_config_values = [
        ('obsidian_entrypoint_path_str', 'ci/test_vault/filtering/home.md'),
        ('module_config/get_file_list/include_glob/value', ['filtering/**/*']),
        ('module_config/get_file_list/exclude_glob/value', ['*.pdf','/filtering/excl/**/*']),
        ('copy_vault_to_tempdir', False),
    ]
    def test_include_folder(self):
        print(yaml.dump(self.testcase_config))
        self.scribe('Exclude folder')
        issues, actual_files = check_md_output('md/filtering', ['neutral'])
        self.assertEqual(len(issues), 0, msg=f"Issues found with filtering\n{actual_files}\n{yaml.dump(issues)}")

    def test_exclude_pdf(self):
        self.scribe('Exclude text files')
        issues, actual_files = check_md_output('md/filtering/neutral', ['neutral.md'])
        self.assertEqual(len(issues), 0, msg=f"Issues found with filtering\n{actual_files}\n{yaml.dump(issues)}")


if __name__ == '__main__':
    # Args
    run_setup = False
    run_cleanup = False
    for i, v in enumerate(sys.argv):
        if v == '-r':
            run_setup = True
        if v == '-c':
            run_cleanup = True
        if v == 'v':
            verbose = True

    if USE_PIP_INSTALL:
        subprocess.call(['pip', 'install', '.', '--upgrade'])

    # get paths
    paths = get_paths()
    
    # Create temp dir
    os.chdir(paths['root'])
    paths['temp_dir'].mkdir(exist_ok=True)

    # Start webserver
    # ----------------------------
    # defer context for webserver
    with ExitStack() as stack:
        webserver_process = subprocess.Popen(['python', '-m', 'http.server', '--directory', paths['html_output_folder'], '8088'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # close server *always* on exit
        stack.callback(partial(webserver_process.terminate))
        stack.callback(partial(print, 'DEFERRED: closed webserver', flush=True))

        time.sleep(0.1)
        print(f"WEBSERVER: started on http://localhost:8088 in {paths['html_output_folder']}", flush=True)

        # Run tests
        # ----------------------------
        unittest.main(failfast=True)

