from .lib import OpenIncludedFile
from .PicknickBasket import PicknickBasket

import time
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from html import escape

def CreateRssFeed():
    pb = PicknickBasket()
    pb.config = {
        'toggles': {
            'features': {
                'rss': {
                    'enabled': True,
                    'host_root': 'https://obsidian-html.github.io/',
                    'styling': {
                        'show_icon': True
                    },
                    'channel': {
                        'title': 'ObsidianHtml/Documentation',
                        'website_link': 'https://obsidian-html.github.io',
                        'description': 'The documentation site of ObsidianHtml, a package used to convert Obsidian notes to proper markdown and static HTML websites.',
                        'language_code': 'en-us',
                        'managing_editor': 'collector@dwrolvink.com',
                        'web_master': 'collector@dwrolvink.com'
                    },
                    'items': {
                        'match_on_key_values': [['tags','type/news']],
                        'publish_data_key': ['tags','date/'],
                        'item_description_selector': ['first-paragraphs', 2],
                        'item_title_selector': ['h1', 'file_plus_first_folder'],
                        'start_in_subfolder': 'Log',
                        'exclude_folders': ['.git', 'md', 'index_from_tags', 'obs.html','__src'],
                        'exclude_files': ['not_created.html', 'index.html']
                    }
                }
            }
        }
    }

    # Setup
    # ----------------------------------------------------------------------
    rss_channel_template = OpenIncludedFile('rss_channel_template.xml')
    rss_item_template = OpenIncludedFile('rss_item_template.xml')
    now_rss_format = datetime.now().strftime("%a, %d %b %Y %H:%M:%S ") + time.tzname[0]
    html_folder = Path('../obsidian-html.github.io/').resolve()

    host = pb.gc('toggles','features','rss','host_root')
    if host[-1] != '/':
        host += '/'    

    # Set entry folder for collecting notes
    entry_folder = html_folder
    sis = pb.gc('toggles','features','rss','items','start_in_subfolder')
    if sis != '':
        entry_folder = html_folder.joinpath(sis)
    else:
        entry_folder = html

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
        'last_build_date': now_rss_format
    }
    for key, value in lut.items():
        rss_channel_template = rss_channel_template.replace('{'+key+'}', value)

    # Compile Items
    # ----------------------------------------------------------------------
    # define excluded folders
    excluded_folders = []
    for ef in pb.gc('toggles','features','rss','items','exclude_folders'):
        if ef[-1] != '/':
            ef += '/'
        excluded_folders.append(html_folder.joinpath(ef).resolve())

    # define excluded files
    excluded_files = []
    for ef in pb.gc('toggles','features','rss','items','exclude_files'):
        excluded_files.append(html_folder.joinpath(ef).resolve())

    # add items
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
        #print(path)
        with open(path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html5lib')
        
        # compile description
        description = ''
        limit = 2
        paragraphs = soup.body.find_all('p')
        len_paragraphs = len(paragraphs)
        for i in range(2):
            if i < len_paragraphs:
                description += paragraphs[i].text + '\n\n'

        # get title
        # title = soup.body.find('h1')
        # if title is not None:
        #     title = title.text
        # else:
        title = path.stem #path.parent.name + '/' + path.stem
        
        # get publish date
        

        # link
        link = host + path.relative_to(html_folder).as_posix()

        lut = {
            'title': title,
            'link': link.replace(' ', '%20'),
            'description': description,
            'publish_date': now_rss_format,
            'guid': link,
            'enclosure': ''
        }
        rss_item = rss_item_template
        for key, value in lut.items():
            rss_item = rss_item.replace('{'+key+'}', escape(value))
        items += rss_item + '\n'
   
    rss_channel_template = rss_channel_template.replace('{items}', items)
    
    with open('../obsidian-html.github.io/obs.html/rss/feed.xml', 'w', encoding='utf-8') as f:
        f.write(rss_channel_template)

