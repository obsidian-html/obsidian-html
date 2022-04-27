from os import listdir
from os.path import isfile, join

from .lib import OpenIncludedFile, GetIncludedResourcePath

# This var contains all the svg data
# We load them here so that the callout extension doesn't have to load them
# every time it is called. These can be reused by ObsidianHtml, that's why this
# code is here and not in CallOutExtension.py
shared_obsidian_svgs = {}

# get svgs
svg_dir = GetIncludedResourcePath('svgs')
for svg_file_name in [f for f in listdir(svg_dir) if isfile(join(svg_dir, f))]:     # get all files in svg_dir
    svg_name = svg_file_name.replace('.html','')
    shared_obsidian_svgs[svg_name] = OpenIncludedFile(f'svgs/{svg_file_name}')

shared_obsidian_svgs['default'] = shared_obsidian_svgs['note']