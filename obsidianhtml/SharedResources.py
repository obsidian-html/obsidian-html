from os import listdir
from os.path import isfile, join

from .lib import OpenIncludedFile, GetIncludedResourcePath


shared_obsidian_svgs = {}
svg_dir = GetIncludedResourcePath('svgs')

for svg_file_name in [f for f in listdir(svg_dir) if isfile(join(svg_dir, f))]:
    svg_name = svg_file_name.replace('.html','')
    shared_obsidian_svgs[svg_name] = OpenIncludedFile(f'svgs/{svg_file_name}')

shared_obsidian_svgs['default'] = shared_obsidian_svgs['note']