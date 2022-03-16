import re                   # regex string finding/replacing
from pathlib import Path    # 
import frontmatter          # remove yaml frontmatter from md files
import urllib.parse         # convert link characters like %
import warnings
import shutil               # used to remove a non-empty directory, copy files
from .lib import DuplicateFileNameInRoot, GetObsidianFilePath


class HtmlLink:
    pb = None
    dst_page_file_path = None
    src_page_file_path = None

    def __init__(self, pb):
        self.pb = pb

    def Source(self, src_page_file_path):
        self.src_page_file_path = src_page_file_path

    def Target(self, dst_page_file_path):
        self.dst_page_file_path = dst_page_file_path

    # Scenarios:
    # - relative_path_html