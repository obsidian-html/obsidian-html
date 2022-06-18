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
    name = ''
    fo = None
    
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

    def __init__(self, pb, url, page_path, root_path, relative_path_md = True, url_unquote=False):
        # Set attributes
        self.pb = pb
        self.relative_path_md = relative_path_md    # Whether the markdown interpreter assumes relative path when no / at the beginning of a link
        self.page_path = page_path
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

        # Fetch file object. If this succeeds it means we can copy it over to the output
        self.GetFileObject()

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
        if self.url.startswith('mailto:'):
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

    def GetFileObject(self):
        #self.name = self.url.split('/')[-1]
        url = self.url
        res = GetObsidianFilePath(url, self.pb.files, self.pb)
        if res['fo']:
            self.fo = res['fo']
        return