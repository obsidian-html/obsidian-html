from .lib import OpenIncludedFile
from .PicknickBasket import PicknickBasket

import time
from datetime import datetime
from pathlib import Path
import platform

from bs4 import BeautifulSoup
from html import escape
import json
from time import sleep

def ConvertDateToRssFormat(datetime_object):
    return datetime_object.strftime("%a, %d %b %Y %H:%M:%S ") + time.tzname[0]

class RssFeed():
    pb = None

    rss_channel_template = None
    rss_item_template = None
    now_rss_format = None
    
    html_folder = None
    feed_path = None
    host = None
    
    graph = None
    node_lut = None
    
    excluded_folders = None
    excluded_files = None
    include_subfolders = None

    item_match_keys_selector = None
    item_exclude_keys_selector = None
    description_selectors = None
    title_selectors = None

    def __init__(self, pb):
        # Constants
        self.pb = pb
        self.rss_channel_template = OpenIncludedFile('rss/channel_template.xml')
        self.rss_item_template = OpenIncludedFile('rss/item_template.xml')
        self.now_rss_format = datetime.now().strftime("%a, %d %b %Y %H:%M:%S ") + time.tzname[0]
        self.html_folder = pb.paths['html_output_folder']
        self.feed_path = pb.paths['html_output_folder'].joinpath('obs.html/rss/feed.xml')

        # get host and make sure it ends with '/'
        host = pb.gc('toggles','features','rss','host_root')
        if host[-1] != '/':
            host += '/'
        self.host = host

        # get graph.json data and convert to python dict
        graph_path = self.html_folder.joinpath('obs.html/data/graph.json').resolve()
        with open(graph_path, 'r', encoding='utf-8') as f:
            self.graph = json.loads(f.read())

        # Create lookup table to quickly get node information
        node_lut = {}
        for node in self.graph['nodes']:
            node_lut[node['id']] = node
        self.node_lut = node_lut

        # define excluded folders
        excluded_folders = []
        for ef in pb.gc('toggles','features','rss','items','selector','exclude_subfolders'):
            if ef[-1] != '/':
                ef += '/'
            excluded_folders.append(self.html_folder.joinpath(ef).resolve())
        self.excluded_folders = excluded_folders

        # define excluded files
        excluded_files = []
        for ef in pb.gc('toggles','features','rss','items','selector','exclude_files'):
            excluded_files.append(self.html_folder.joinpath(ef).resolve())
        self.excluded_files = excluded_files

        # define include_subfolders
        self.include_subfolders = pb.gc('toggles','features','rss','items','selector','include_subfolders')

        # define item selectors
        self.item_match_keys_selector = pb.gc('toggles','features','rss','items','selector','match_keys')
        self.item_exclude_keys_selector = pb.gc('toggles','features','rss','items','selector','exclude_keys')
        self.description_selectors = pb.gc('toggles','features','rss','items','description','selectors')
        self.title_selectors = pb.gc('toggles','features','rss','items','title','selectors')
        self.publish_date_selectors = pb.gc('toggles','features','rss','items','publish_date','selectors')

    def Compile(self):
        # Setup
        # ----------------------------------------------------------------------
        pb = self.pb

        # Compile Items
        # ----------------------------------------------------------------------
        # keep track of most recent item
        most_recent_publish_date = datetime.min

        # add items
        items = ''
        
        if len(self.include_subfolders) == 0:
            items, most_recent_publish_date = self.get_items(self.html_folder, most_recent_publish_date)
        else:
            for subfolder in self.include_subfolders:
                entry_folder = self.html_folder.joinpath(subfolder).resolve()
                new_items, most_recent_publish_date = self.get_items(entry_folder, most_recent_publish_date)
                items += new_items

        # Fill in channel template
        # ----------------------------------------------------------------------
        lut = {
            'title': pb.gc('toggles','features','rss','channel','title'),
            'website_link': pb.gc('toggles','features','rss','channel','website_link'),
            'description': pb.gc('toggles','features','rss','channel','description'),
            'language_code': pb.gc('toggles','features','rss','channel','language_code'),
            'managing_editor': pb.gc('toggles','features','rss','channel','managing_editor'),
            'web_master': pb.gc('toggles','features','rss','channel','web_master'),
            'publish_date': self.now_rss_format,
            'last_build_date': ConvertDateToRssFormat(most_recent_publish_date),
            'items': items
        }
        rss_channel = self.rss_channel_template
        for key, value in lut.items():
            rss_channel = rss_channel.replace('{'+key+'}', value)
        
        # Write to output
        with open(self.feed_path, 'w', encoding='utf-8') as f:
            f.write(rss_channel)


    def get_items(self, entry_folder, most_recent_publish_date):
        pb = self.pb
        items = ''
        for path in entry_folder.rglob('*'):
            # don't handle dirs
            if path.is_dir():
                continue

            # don't handle anything in excluded folders
            # don't handle excluded files
            excluded = False
            for ef in self.excluded_folders:
                if path.is_relative_to(ef):
                    excluded = True
                    break
            for ef in self.excluded_files:
                if path == ef:
                    excluded = True
                    break
            if excluded:
                continue

            # only handle files that end in .html
            if path.as_posix()[-5:-1] != '.htm':
                continue

            # get html
            with open(path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html5lib')

            # get metadata
            node_el = soup.find('meta',attrs={'name':'node_id'})
            if node_el is None:
                raise Exception('RSS Feed: Meta tag with node_id was not found. If you are using a custom template, make sure that <meta name="node_id" content="{node_id}"> is present in the html header to use this feature.')
            node_id = node_el['content']
            metadata = None
            if node_id != 'none':
                metadata = self.node_lut[node_id]['metadata']

            # exclude: match note on key
            selector = self.item_exclude_keys_selector
            if not selector:
                pass
            elif selector[0] == 'yaml':
                selector_key = selector[1]
                selector_prefixes = selector[2]
                rv = yaml_selector(metadata, selector_key, selector_prefixes)
                if rv:
                    continue
            else:
                raise Exception(f"RSS Feed: get_items(): Selector function {selector[0]} not implemented.")

            # include: match note on key
            selector = self.item_match_keys_selector
            if not selector:
                pass
            if selector[0] == 'yaml':
                selector_key = selector[1]
                if len(selector) > 2:
                    selector_prefixes = selector[2]
                else:
                    selector_prefixes = None

                rv = yaml_selector(metadata, selector_key, selector_prefixes)
                if not rv:
                    continue
            else:
                raise Exception(f"RSS Feed: get_items(): Selector function {selector[0]} not implemented for note selection.")

            # compile description
            description = self.select_value(metadata, soup, path, self.description_selectors)
            if not description:
                print(f"RSS Feed: warning: no description found for note {path}")

            # get title
            title = self.select_value(metadata, soup, path, self.title_selectors)
            if not title:
                print(f"RSS Feed: warning: no title found for note {path}")
            
            # get publish date
            publish_date = self.select_value(metadata, soup, path, self.publish_date_selectors)
            if not publish_date:
                print(f"RSS Feed: warning: no publish_date found for note {path}")

            if pb.gc('toggles','features','rss','items','publish_date','iso_formatted'):
                publish_date = datetime.fromisoformat(publish_date)
            else:
                fs = pb.gc('toggles','features','rss','items','publish_date','format_string')
                if fs:
                    try:
                        publish_date = datetime.strptime(publish_date, fs)
                    except ValueError:
                        raise Exception(f"Don't know how to parse date string. Found date '{publish_date}' does not match format_string '{fs}'.")
                else:
                    raise Exception("Don't know how to parse date string. Iso_formatted is false and format_string is empty.")

            publish_date_str = ConvertDateToRssFormat(publish_date)

            if publish_date > most_recent_publish_date:
                most_recent_publish_date = publish_date

            # link
            link = self.host + path.relative_to(self.html_folder).as_posix()

            lut = {
                'title': title,
                'link': link.replace(' ', '%20'),
                'description': description,
                'publish_date': publish_date_str,
                'guid': link,
                'enclosure': ''
            }
            rss_item = self.rss_item_template
            for key, value in lut.items():
                rss_item = rss_item.replace('{'+key+'}', escape(value))
            items += rss_item + '\n'

            if pb.gc('toggles','verbose_printout'):
                print(f"\tAdded item: '{publish_date_str}', '{title}', '{link}'")

        return [items, most_recent_publish_date]

    def select_value(self, metadata, soup, path, selector_list):
        value = ''

        for selector in selector_list:
            selector_function = selector[0]

            if selector_function == 'first-paragraphs':
                value = selector_first_paragraphs(soup, number_of_paragraphs=selector[1], delimiter=selector[2])

            elif selector_function == 'first-header':
                value = selector_first_header(soup, header_level=selector[1])

            elif selector[0] == 'yaml' or selector[0] == 'yaml_strip':
                selector_key = selector[1]
                if len(selector) > 2:
                    selector_prefixes = selector[2]
                else:
                    selector_prefixes = None

                if selector[0] == 'yaml':
                    value = yaml_selector(metadata, selector_key, selector_prefixes)
                else:
                    value = yaml_selector(metadata, selector_key, selector_prefixes, strip_prefix=True)

            elif selector[0] == 'path':
                print(path, type(path))
                value = selector_path(path, selector[1:])
            else:
                raise Exception(f"RSS Feed: get_items(): Selector function {selector[0]} not implemented.")

            # return if value is not empty
            if value:
                return value
        
        # return empty string if nothing found
        return ''


def yaml_selector(metadata, key, list_item_prefixes=None, strip_prefix=False):
    '''searches the metadata for the key, and returns the value
       + if the key is not found in the metadata, an empty string is returned
       + if list_item_prefix is none, the value of the key is returned as a string, regardless of type.    
       + if list_item_prefix is not none then it will assume the type of the key value is a list.
       - if multiple items, starting with the one of the values in list_item_prefix, exist in a list, the first found is returned as a string.
       - if no items starting with the list_item_prefix exist in the list, an empty string is returned
       - match all items by passing in list_item_prefix=['']
       - if not a list, it will return an empty string.
       + keys multiple levels deep can be encoded by using ':'
    '''

    # return empty string if metadata is none
    if metadata is None:
        return ''

    # select value from key
    value = metadata
    for k in key.split(':'):
        try:
            value = value[k]
        except KeyError:
            return ''

    # return str of value if list_item_prefix is none
    if list_item_prefixes is None:
        return str(value)

    # list_item_prefixes should be a list
    if not isinstance(list_item_prefixes, list):
        raise Exception("yaml_selector: list_item_prefixes should be a list")

    # assume list
    if not isinstance(value, list):
        return ''
    
    # return first matched item
    for item in value:
        for prefix in list_item_prefixes:
            if item.startswith(prefix):
                if strip_prefix:
                    return item.replace(prefix, '', 1)
                else:
                    return item
    
    # no items matched
    return ''

def selector_first_paragraphs(soup, number_of_paragraphs, delimiter):
    value = ''
    paragraphs = soup.body.find_all('p')
    len_paragraphs = len(paragraphs)
    for i in range(number_of_paragraphs):
        if i < len_paragraphs:
            value += paragraphs[i].text + str(delimiter)
    
    return value

def selector_first_header(soup, header_level):
    value = ''
    header = soup.body.find('h'+str(header_level))
    if header is None:
        return ''
    return header.text

def selector_path(path, args):
    # ['path', [parent, 1], '/ ', ['stem']]

    value = ''
    for arg in args:
        if isinstance(arg, list):
            # Get the name of n-th level parent folder
            if arg[0] == 'parent':
                el = path
                for i in range(arg[1]):
                    el = el.parent
                value += el.name
            
            # Get filename minus suffix
            elif arg[0] == 'stem':
                value += path.stem
            else:
                raise Exception(f"Rss Feed: selector_path(): unknown path selector '{arg[0]}'.")
        else:
            value += arg

    return value