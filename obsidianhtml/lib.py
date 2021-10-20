import re                   # regex string finding/replacing
from pathlib import Path    # 
import frontmatter          # remove yaml frontmatter from md files
import urllib.parse         # convert link characters like %
import warnings
import shutil               # used to remove a non-empty directory, copy files
from string import ascii_letters, digits
 
# Lookup tables
image_suffixes = ['jpg', 'jpeg', 'gif', 'png', 'bmp']

class DuplicateFileNameInRoot(Exception):
    pass

def GetObsidianFilePath(link, file_tree):
    # Remove possible alias suffix, folder prefix, and add '.md' to get a valid lookup key
    parts = link.split('|')[0].split('/')[-1].split('#')
    filename = parts[0]
    header = ''
    if len(parts) > 1:
        header = parts[1]

    if filename[-3:] != '.md':
        filename += '.md'
        
    # Return tuple
    if filename not in file_tree.keys():
        return (filename, False)

    return (filename, file_tree[filename], header)

def ConvertTitleToMarkdownId(title):
    idstr = title.lower().strip()
    idstr = idstr.replace(' ', '-')
    while '--' in idstr:
        idstr = idstr.replace('--', '-')
    idstr = "".join([ch for ch in idstr if ch in (ascii_letters + digits + ' -')])
    return idstr