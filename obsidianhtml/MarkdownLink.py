import re                   # regex string finding/replacing
from pathlib import Path    # 
import frontmatter          # remove yaml frontmatter from md files
import urllib.parse         # convert link characters like %
import warnings
import shutil               # used to remove a non-empty directory, copy files
from .lib import DuplicateFileNameInRoot, GetObsidianFilePath

class MarkdownLink:
    """Helper class to abstract away a lot of recurring path-testing logic."""
    url = ''
    
    isValid = True
    isExternal = False
    isAnchor = False
    inRoot = False
    suffix = ''

    src_path = None
    rel_src_path = None
    rel_src_path_posix = None
    page_path = None
    root_path = None

    query_delimiter = ''
    query = ''

    def __repr__(self):
        return f"MarkdownLink(\n\turl = \"{self.url}\", \n\tsuffix = '{self.suffix}', \n\tisValid = {self.isValid}, \n\tisExternal = {self.isExternal}, \n\tinRoot = {self.inRoot}, \n\tsrc_path = {self.src_path}, \n\trel_src_path = {self.rel_src_path}, \n\trel_src_path_posix = {self.rel_src_path_posix}, \n\tpage_path = {self.page_path}, \n\troot_path = {self.root_path} \n)"    

    def __init__(self, url, page_path, root_path, relative_path_md = True, url_unquote=False):
        # Set attributes
        self.relative_path_md = relative_path_md    # Whether the markdown interpreter assumes relative path when no / at the beginning of a link
        self.page_path = page_path
        self.root_path = root_path
        self.url = url
        if url_unquote:
            self.url = urllib.parse.unquote(self.url)

        # Split the query part of "link#query" into self.query
        # Self.url will be the "link" part.
        self.SplitQuery()

        # Url cannot be ''
        # If more tests are needed, they can be added here.
        self.TestisValid()

        # Get suffix, and set suffix to .md if no suffix is present
        self.ParseType()

        # Set self.isExternal if the file contains certain character sequences such as ://
        self.TestIsExternal()
        
        # Set src and rel_src paths
        if self.isValid and self.isExternal == False:
            self.ParsePaths()

    def SplitQuery(self):
        url = self.url
        
        if len(url.split('#')) > 1:
            self.url = url.split('#')[0]
            self.query = url.split('#', 1)[1]
            self.query_delimiter = '#'
            return
        if len(url.split('?')) > 1:
            self.url = url.split('?')[0]
            self.query = url.split('?', 1)[1]
            self.query_delimiter = '?'
            return     

    def TestisValid(self):
        if self.url == '':
            self.isValid = False
            return

    def TestIsExternal(self):
        # Test if \\ // S:\ http(s)://
        if '\\\\' in self.url:
            self.isExternal = True
        if '://' in self.url:
            self.isExternal = True
        if ':\\' in self.url:
            self.isExternal = True

    def ParseType(self):
        if self.url.startswith('#'):
            self.isAnchor = True
            return

        # Convert path/file to path/file.md
        self.suffix = Path(self.url).suffix
        if self.suffix == '':
            self.url += '.md'
            self.suffix = '.md'

    def ParsePaths(self):
        # /path/file.md --> root_path + url
        # path/file.md --> page_path + url
        if self.url[0] == '/':
            self.src_path = self.root_path.joinpath(self.url[1:]).resolve()
        else:
            if self.relative_path_md:
                self.src_path = self.page_path.parent.joinpath(self.url).resolve()
            else:
                self.src_path = self.root_path.joinpath(self.url).resolve()
            
        # Determine if relative to root
        if self.src_path.is_relative_to(self.root_path):
            self.inRoot = True
        else:
            return

        # Determine relative path
        self.rel_src_path = self.src_path.relative_to(self.root_path)
        self.rel_src_path_posix = self.rel_src_path.as_posix()
