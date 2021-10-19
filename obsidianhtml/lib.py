import re                   # regex string finding/replacing
from pathlib import Path    # 
import frontmatter          # remove yaml frontmatter from md files
import urllib.parse         # convert link characters like %
import warnings
import shutil               # used to remove a non-empty directory, copy files
 
# Lookup tables
image_suffixes = ['jpg', 'jpeg', 'gif', 'png', 'bmp']

class DuplicateFileNameInRoot(Exception):
    pass

def GetObsidianFilePath(link, file_tree):
    # Remove possible alias suffix, folder prefix, and add '.md' to get a valid lookup key
    filename = link.split('|')[0].split('/')[-1].split('#')[-1]

    if filename[-3:] != '.md':
        filename += '.md'
        
    # Return tuple
    if filename not in file_tree.keys():
        return (filename, False)

    return (filename, file_tree[filename])
    