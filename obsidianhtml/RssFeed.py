from .lib import OpenIncludedFile
from .PicknickBasket import PicknickBasket

import time
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from html import escape
import json

def ConvertDateToRssFormat(datetime_object):
    return datetime_object.strftime("%a, %d %b %Y %H:%M:%S ") + time.tzname[0]

class RssFeed():
    pb = None

    def __init__(self, pb):
        self.pb = pb

    def Compile(self):
        # Setup
        # ----------------------------------------------------------------------
        pb = self.pb

        rss_channel_template = OpenIncludedFile('rss/channel_template.xml')
        rss_item_template = OpenIncludedFile('rss/item_template.xml')

        now_rss_format = datetime.now().strftime("%a, %d %b %Y %H:%M:%S ") + time.tzname[0]
        html_folder = pb.paths['html_output_folder']
        feed_path = pb.paths['html_output_folder'].joinpath('obs.html/rss/feed.xml')

        host = pb.gc('toggles','features','rss','host_root')
        if host[-1] != '/':
            host += '/'

        # get graph.json data and convert to python dict
        graph_path = html_folder.joinpath('obs.html/data/graph.json').resolve()
        with open(graph_path, 'r', encoding='utf-8') as f:
            graph = json.loads(f.read())
        node_lut = {}
        for node in graph['nodes']:
            node_lut[node['id']] = node

        # Compile Items
        # ----------------------------------------------------------------------
        # define excluded folders
        excluded_folders = []
        for ef in pb.gc('toggles','features','rss','items','selector','exclude_folders'):
            if ef[-1] != '/':
                ef += '/'
            excluded_folders.append(html_folder.joinpath(ef).resolve())

        # define excluded files
        excluded_files = []
        for ef in pb.gc('toggles','features','rss','items','selector','exclude_files'):
            excluded_files.append(html_folder.joinpath(ef).resolve())

        # keep track of most recent item
        most_recent_publish_date = datetime.min

        # add items
        items = ''
        include_subfolders = pb.gc('toggles','features','rss','items','selector','include_subfolders')
        if len(include_subfolders) == 0:
            items, most_recent_publish_date = self.get_items(pb, html_folder, excluded_folders, excluded_files, node_lut, host, html_folder, rss_item_template, most_recent_publish_date)
        else:
            for subfolder in include_subfolders:
                entry_folder = html_folder.joinpath(subfolder).resolve()
                new_items, most_recent_publish_date = self.get_items(pb, entry_folder, excluded_folders, excluded_files, node_lut, host, html_folder, rss_item_template, most_recent_publish_date)
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
            'publish_date': now_rss_format,
            'last_build_date': ConvertDateToRssFormat(most_recent_publish_date),
            'items': items
        }
        for key, value in lut.items():
            rss_channel_template = rss_channel_template.replace('{'+key+'}', value)
        
        # Write to output
        with open(feed_path, 'w', encoding='utf-8') as f:
            f.write(rss_channel_template)

    def get_items(self, pb, entry_folder, excluded_folders, excluded_files, node_lut, host, html_folder, rss_item_template, most_recent_publish_date):
        items = ''
        for path in entry_folder.rglob('*'):
            # don't handle dirs
            if path.is_dir():
                continue

            # don't handle anything in excluded folders
            # don't handle excluded files
            excluded = False
            for ef in excluded_folders:
                if path.is_relative_to(ef):
                    excluded = True
                    break
            for ef in excluded_files:
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
            node_id = soup.find('meta',attrs={'name':'node_id'})['content']
            metadata = None
            if node_id != 'none':
                metadata = node_lut[node_id]['metadata']
            
            # compile description
            description = ''
            limit = 2
            paragraphs = soup.body.find_all('p')
            len_paragraphs = len(paragraphs)
            for i in range(2):
                if i < len_paragraphs:
                    description += paragraphs[i].text + '<br/><br/>'

            # get title
            # title = soup.body.find('h1')
            # if title is not None:
            #     title = title.text
            # else:
            title = path.stem #path.parent.name + '/' + path.stem
            
            # get publish date
            publish_date = ''
            key, prefix = pb.gc('toggles','features','rss','items','publish_date','selector')
            if prefix is not None and prefix != '':
                if key in metadata:
                    for entry in metadata[key]:
                        if entry.startswith(prefix):
                            publish_date = entry.replace(prefix, '')
                else:
                   raise Exception(f"Could not fetch publish date because metadata key '{key}' does not exist in note '{path}'") 
            print(publish_date)

            if pb.gc('toggles','features','rss','items','publish_date','iso_formatted'):
                publish_date = datetime.fromisoformat(publish_date)
            else:
                raise Exception("Don't know how to parse date string")

            publish_date_str = ConvertDateToRssFormat(publish_date)

            if publish_date > most_recent_publish_date:
                most_recent_publish_date = publish_date

            # link
            link = host + path.relative_to(html_folder).as_posix()

            lut = {
                'title': title,
                'link': link.replace(' ', '%20'),
                'description': description,
                'publish_date': publish_date_str,
                'guid': link,
                'enclosure': ''
            }
            rss_item = rss_item_template
            for key, value in lut.items():
                rss_item = rss_item.replace('{'+key+'}', escape(value))
            items += rss_item + '\n'

        return [items, most_recent_publish_date]