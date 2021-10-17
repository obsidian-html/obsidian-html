import sys                  # commandline arguments
import os                   #
import shutil               # used to remove a non-empty directory, copy files
import re                   # regex string finding/replacing
from pathlib import Path    # 
import frontmatter          # remove yaml frontmatter from md files
import markdown             # convert markdown to html
import urllib.parse         # convert link characters like %
import warnings
 
# python run.py 'C:\Users\Installer\OneDrive\Obsidian\Notes' "C:\Users\Installer\OneDrive\Obsidian\Notes\Devfruits Notes.md" "output/md" "output/html" "Devfruits/Notes"

class DuplicateFileNameInRoot(Exception):
    pass

class MarkdownPage:
    page = None            # Pure markdown code read from src file
    yaml = None             # Yaml is stripped from the src file and saved here
    codeblocks = None       # used to safely store ```codeblock content
    codelines = None        # Used to safely store `codeline` content
    links = None            # Used to recurse to any page linked to by this page

    src_path  = None        # Path() object of src file
    rel_src_path  = None    # Path() object relative to given markdown root folder (src_folder_path)
    src_folder_path = None  # Path() object of given markdown root folder
    dst_path = None         # Path() object of destination file

    def __init__(self, src_path, src_folder_path):
        self.src_path = src_path
        self.src_folder_path = src_folder_path
        self.rel_src_path = self.src_path.relative_to(src_folder_path)

        self.links = []
        self.codeblocks = []
        self.codelines = []
        
        # Load contents of entrypoint and strip frontmatter yaml.
        page = frontmatter.load(str(src_path))
        self.page = page.content
        self.yaml = page

    def SetDestinationPath(self, dst_folder_path, entrypoint_src_path):
        if entrypoint_src_path == self.src_path:
            self.dst_path = dst_folder_path.joinpath('index.md')
        else:
            self.dst_path = dst_folder_path.joinpath(self.rel_src_path.as_posix())
        self.rel_dst_path = self.dst_path.relative_to(dst_folder_path)

    def StripCodeSections(self):
        self.codeblocks = re.findall("^```([\s\S]*?)```$", self.page, re.MULTILINE)
        for i, match in enumerate(self.codeblocks):
            self.page = self.page.replace("```"+match+"```", f'%%%codeblock-placeholder-{i}%%%')
            
        self.codelines = re.findall("`(.*?)`", self.page)
        for i, match in enumerate(self.codelines):
            self.page = self.page.replace("`"+match+"`", f'%%%codeline-placeholder-{i}%%%')
           
    def RestoreCodeSections(self):
        for i, value in enumerate(self.codeblocks):
            self.page = self.page.replace(f'%%%codeblock-placeholder-{i}%%%', f"```{value}```\n")
        for i, value in enumerate(self.codelines):
            self.page = self.page.replace(f'%%%codeline-placeholder-{i}%%%', f"`{value}`")    

class MarkdownLink:
    url = ''
    
    isValid = True
    isExternal = False
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

    def __init__(self, url, page_path, root_path, url_unquote=False):
        self.url = url
        if url_unquote:
            self.url = urllib.parse.unquote(self.url)
        self.SplitQuery()

        self.page_path = page_path
        self.root_path = root_path
        
        self.TestisValid()
        self.ParseType()
        self.TestIsExternal()
        
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
        self.suffix = Path(self.url).suffix

        # Convert path/file to path/file.md
        if self.suffix == '':
            self.url += '.md'
            self.suffix = '.md'

    def ParsePaths(self):
        # /path/file.md --> root_path + url
        # path/file.md --> page_path + url
        if self.url[0] == '/':
            self.src_path = self.root_path.joinpath(self.url[1:]).resolve()
        else:
            if relative_path_md:
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

def ConvertObsidianPageToMarkdownPage(page_path_str, include_depth=0):
    page_path = Path(page_path_str).resolve()

    if page_path.exists() == False:
        return
    if page_path.suffix != '.md':
        return

    # -- Load contents
    md = MarkdownPage(page_path, root_folder_path)
    md.SetDestinationPath(md_folder_path, entrypoint_path)

    # -- Get page depth
    page_folder_depth = md.rel_src_path.as_posix().count('/')

    # -- Replace code blocks with placeholders so they aren't altered
    # They will be restored at the end
    md.StripCodeSections() 

    # -- Add newline between paragraph and lists
    buffer = ''
    prev_is_list_line = False
    for i, line in enumerate(md.page.split('\n')):
        current_is_list_line = False
        clean_line = line.strip()
        if len(clean_line) == 0:
            current_is_list_line = False
        elif clean_line[0] == '-':
            current_is_list_line = True
        if current_is_list_line and (prev_is_list_line == False):
            buffer += '\n'
        buffer += '\n' + line
        prev_is_list_line = current_is_list_line
    md.page = buffer

    # -- Convert Obsidian type img links to proper md image links
    # Further conversion will be done in the block below
    for link in re.findall("(?<=\!\[\[)(.*?)(?=\])", md.page):
        new_link = '![]('+link+')'

        # Obsidian page inclusions use the same tag...
        # Skip if we don't match image suffixes. Inclusions are handled at the end.
        if len(link.split('.')) == 1 or link.split('.')[-1] not in image_suffixes:
            new_link = f'<inclusion href="{link}" />'

        safe_link = re.escape('![['+link+']]')
        md.page = re.sub(safe_link, new_link, md.page)

    # -- Handle local image links (copy them over to output)
    for link in re.findall("(?<=\!\[\]\()(.*)(?=\))", md.page):
        # Only handle local image files (images located in the root folder)
        if urllib.parse.unquote(link).split('/')[-1] not in files.keys():
            continue

        # Build relative paths
        src_file_path_str = files[urllib.parse.unquote(link).split('/')[-1]]['fullpath']
        relative_path = Path(src_file_path_str).relative_to(root_folder_path)
        dst_file_path = md_folder_path.joinpath(relative_path)

        # Create folders if necessary
        dst_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy file over
        shutil.copyfile(src_file_path_str, dst_file_path)

        # Adjust link in page
        file_name = urllib.parse.unquote(link)
        relative_path = relative_path.as_posix()
        relative_path = ('../' * page_folder_depth) + relative_path
        new_link = '![]('+urllib.parse.quote(relative_path)+')'
        safe_link = re.escape('![]('+link+')')
        md.page = re.sub(safe_link, new_link, md.page)

    # -- Proper markdown links
    # And while we are busy, change the path to point to the full relative path
    proper_links = re.findall("(?<=[^\[]\]\().+?(?=\))", md.page)
    for l in proper_links:
        # Get the filename
        file_name = urllib.parse.unquote(l)

        # Determine if file is markdown
        isMd = False
        if file_name[-3:] == '.md':
            isMd = True
        if Path(file_name).suffix == '':
            isMd = True
            file_name += '.md'
   
        if isMd:
            # Add to list to recurse to the link later
            md.links.append(file_name)

        # Don't continue processing for non local files
        if file_name.split('/')[-1] not in files.keys():
            continue

        # Determine paths
        filepath = files[file_name.split('/')[-1]]['fullpath']
        relative_path_posix = Path(filepath).relative_to(root_folder_path).as_posix()
        dst_filepath = md_folder_path.joinpath(relative_path_posix)

        if isMd:
            if relative_path_posix == rel_entrypoint_path.as_posix():      
                relative_path_posix = 'index.md'

        # Change the link in the markdown to link to the relative path
        relative_path_posix = ('../' * page_folder_depth) + relative_path_posix
        new_link = ']('+relative_path_posix+')'

        safe_link = re.escape(']('+l+')')
        md.page = re.sub(f"(?<![\[\(])({safe_link})", new_link, md.page)

        if isMd == False:
            # Copy file over to new location
            shutil.copyfile(filepath, dst_filepath)

        
    # -- Replace Obsidian links with proper markdown
    # This is any string in between [[ and ]], e.g. [[My Note]]
    md_links = re.findall("(?<=\[\[).+?(?=\])", md.page)
    for l in md_links:
        # A link in Obsidian can have the format 'filename|alias'
        # If a link does not have an alias, the link name will function as the alias.
        parts = l.split('|')
        filename = parts[0].split('/')[-1]
        alias = filename
        if len(parts) > 1:
            alias = parts[1]

        # Split #Chapter
        hashpart = ''
        parts = filename.split('#')
        if len(parts) > 1:
            filename = parts[0]
            hashpart = parts[1]

        isMd = False
        if filename[-3:] == '.md':
            isMd = True
        else:
            # Always assume that Obsidian filenames are links
            # This is the default behavior. Use proper markdown to link to files
            filename += '.md'

        md.links.append(filename)

        # Links can be made in Obsidian without creating the note.
        # When we link to a nonexistant note, link to the not_created.md placeholder instead.
        if filename not in files.keys():
            relative_path_posix = '/not_created.md'
        else:
            # Obtain the full path of the file in the directory tree
            # e.g. 'C:\Users\Installer\OneDrive\Obsidian\Notes\Work\Harbor Docs.md'
            full_path = files[filename]['fullpath']
            relative_path_posix = Path(full_path).relative_to(root_folder_path).as_posix()
            if relative_path_posix == rel_entrypoint_path.as_posix():   
                relative_path_posix = 'index.md'

            relative_path_posix = ('../' * page_folder_depth) +  relative_path_posix

        newlink = urllib.parse.quote(relative_path_posix)

        if hashpart != '':
            hashpart = hashpart.replace(' ', '-').lower()
            newlink += f'#{hashpart}'

        # Replace Obsidian link with proper markdown link
        md.page = md.page.replace('[['+l+']]', f"[{alias}]({newlink})")


    # -- Fix newline issue by adding three spaces before any newline
    md.page = md.page.replace("\n", "   \n")

    # -- Insert markdown links for bare http(s) links (those without the [name](link) format).
    # Cannot start with [, (, nor "
    for l in re.findall("(?<![\[\(\"])(http.[^\s]*)", md.page):
        new_md_link = f"[{l}]({l})"
        safe_link = re.escape(l)
        md.page = re.sub(f"(?<![\[\(])({safe_link})", new_md_link, md.page)

    # -- Remove inline tags, like #ThisIsATag
    # Inline tags are # connected to text (so no whitespace nor another #)
    for l in re.findall("(?<!\S)#[^\s#`]+", md.page):
        tag = l.replace('.', '').replace('#', '')
        new_md_str = f"**{tag}**"
        safe_str = re.escape(l)
        md.page = re.sub(safe_str, new_md_str, md.page)

    # -- Add inclusions
    for l in re.findall(r'^(\<inclusion href="[^"]*" />)', md.page, re.MULTILINE):
        link = l.replace('<inclusion href="', '').replace('" />', '')
        print('---', include_depth, l, link)
        link_lookup = GetObsidianFilePath(link)

        if link_lookup == False:
            md.page = md.page.replace(l, f"> **obsidian-html error:** Could not find page {link}.")
            continue
        
        md.links.append(link_lookup[1]['fullpath'])

        if include_depth > 3:
            md.page = md.page.replace(l, f"[{link}]({link_lookup[1]['fullpath']}).")
            continue

        included_page = ConvertObsidianPageToMarkdownPage(link_lookup[1]['fullpath'], include_depth=include_depth + 1)
        md.page = md.page.replace(l, included_page.page)

    # -- Restore codeblocks/-lines
    md.RestoreCodeSections()

    return md

def recurseObisidianToMarkdown(page_path_str):
    md = ConvertObsidianPageToMarkdownPage(page_path_str)

    # -- Save file
    # Create folder if necessary
    md.dst_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write markdown
    with open(md.dst_path, 'w', encoding="utf-8") as f:
        f.write(md.page)

    # -- Recurse for every link in the current page
    for l in md.links:
        link = GetObsidianFilePath(l)
        if link == False or link[1]['processed'] == True:
            continue
        link_path = link[0]

        # Mark the file as processed so that it will not be processed again at a later stage
        files[link_path]['processed'] = True         

        # Convert the note that is linked to
        if verbose_printout:
            print(f"converting {files[link_path]['fullpath']} (parent {page_path})")
        recurseObisidianToMarkdown(files[link_path]['fullpath'])

def GetObsidianFilePath(link):
    # Remove possible alias suffix, folder prefix, and add '.md' to get a valid lookup key
    filename = link.split('|')[0].split('/')[-1].split('#')[-1]

    if filename[-3:] != '.md':
        filename += '.md'
        
    # Skip non-existent notes and notes that have been processed already
    if filename not in files.keys():
        return False

    return (filename, files[filename])
    
def ConvertMarkdownPageToHtmlPage(page_path_str):
    page_path = Path(page_path_str).resolve()

    if page_path.exists() == False:
        return
    if page_path.suffix != '.md':
        return

    # Load contents 
    md = MarkdownPage(page_path, md_folder_path)
    md.SetDestinationPath(html_output_folder_path, md_to_html_entrypoint_path)

    # Replace code blocks with placeholders so they aren't altered
    # They will be restored at the end
    md.StripCodeSections()     

    # Get all markdown links. 
    # This is any string in between '](' and  ')'
    proper_links = re.findall("(?<=\]\().+?(?=\))", md.page)
    for l in proper_links:
        # Init link
        link = MarkdownLink(l, page_path, md_folder_path, url_unquote=True)

        # Don't process in the following cases
        if link.isValid == False or link.isExternal == True: 
            continue

        isMd = False
        filename = link.src_path.name
        if filename[-3:] == '.md':
            isMd = True
        if Path(filename).suffix == '':
            isMd = True
            #link.url += '.md'
            #link.ParsePaths()
            filename += '.md'

        # Copy non md files over wholesale, then we're done for that kind of file
        if link.suffix != '.md' and link.suffix not in image_suffixes:
            html_output_folder_path.joinpath(link.rel_src_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(link.src_path, html_output_folder_path.joinpath(link.rel_src_path))
            continue

        # Not created clause
        if link.url.split('/')[-1] == 'not_created.md':
            new_link = '](/not_created.html)'
        else:
            if link.rel_src_path_posix not in files.keys():
                continue

            md.links.append(link.rel_src_path_posix)

            # Local link found, update link suffix from .md to .html
            query_part = ''
            if link.query != '':
                query_part = link.query_delimiter + link.query 
            new_link = f']({html_url_prefix}/{link.rel_src_path_posix[:-3]}.html{query_part})'
            
        # Update link
        safe_link = re.escape(']('+l+')')
        md.page = re.sub(safe_link, new_link, md.page)

    # Handle local image links (copy them over to output)
    # ----
    for link in re.findall("(?<=\!\[\]\()(.*?)(?=\))", md.page):
        l = urllib.parse.unquote(link)
        full_link_path = page_path.parent.joinpath(l).resolve()
        rel_path = full_link_path.relative_to(md_folder_path)

        # Only handle local image files (images located in the root folder)
        # Doublecheck, who knows what some weird '../../folder/..' does...
        if rel_path.as_posix() not in files.keys():
            if warn_on_skipped_image:
                warnings.warn(f"Image {str(full_link_path)} treated as external and not imported in html")            
            continue

        # Copy src to dst
        dst_path = html_output_folder_path.joinpath(rel_path)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(full_link_path, dst_path)

        # Adjust link in page
        new_link = '![]('+urllib.parse.quote(rel_path.as_posix())+')'
        safe_link = re.escape('![](/'+link+')')
        md.page = re.sub(safe_link, new_link, md.page)
   

    # Restore codeblocks/-lines
    # ----
    md.RestoreCodeSections()

    # Convert markdown to html
    # ----
    extension_configs = {
    'codehilite ': {
        'linenums': True
    }}
    html_body = markdown.markdown(md.page, extensions=['extra', 'codehilite', 'toc'], extension_configs=extension_configs)

    # Tag external links
    for l in re.findall(r'(?<=\<a href=")([^"]*)', html_body):
        if l == '':
            continue
        if l[0] == '/':
            # Internal link, skip
            continue

        new_str = f"<a href=\"{l}\" class=\"external-link\""
        safe_str = f"<a href=\"{l}\""
        html_body = html_body.replace(safe_str, new_str)

    # Tag not created links
    html_body = html_body.replace('<a href="/not_created.html">', '<a href="/not_created.html" class="nonexistent-link">')

    # Wrap body html in valid html structure from template
    html = html_template.replace('{content}', html_body).replace('{title}', site_name).replace('{html_url_prefix}', html_url_prefix)

    # Save file
    # ---- 
    md.dst_path.parent.mkdir(parents=True, exist_ok=True)   
    html_dst_path_posix = md.dst_path.as_posix()[:-3] + '.html' 

    # Write html
    with open(html_dst_path_posix, 'w', encoding="utf-8") as f:
        f.write(html)   

    # Recurse for every link in the current page
    for l in md.links:
        # these are of type rel_path_posix
        link_path = l
        
        # Skip non-existent notes and notes that have been processed already
        if link_path not in files.keys():
            continue
        if files[link_path]['processed'] == True:
            continue
        if files[link_path]['fullpath'][-3:] != '.md':
            continue        

        # Mark the file as processed so that it will not be processed again at a later stage
        files[link_path]['processed'] = True  

        # Convert the note that is linked to
        if verbose_printout:
            print("html: converting ", files[link_path]['fullpath'], " (parent ", md.src_path, ")")

        hmm = ConvertMarkdownPageToHtmlPage(files[link_path]['fullpath'])  


# Config
# ------------------------------------------
# Toggles
toggle_compile_html = True
toggle_compile_md = True
verbose_printout = False
allow_duplicate_filenames_in_root = False
warn_on_skipped_image = True
no_clean = False
relative_path_md = True                        # Whether the markdown interpreter assumes relative path when no / at the beginning of a link

# Lookup tables
image_suffixes = ['jpg', 'jpeg', 'gif', 'png', 'bmp']

# Input
# ------------------------------------------
if '-h' in sys.argv or len(sys.argv) < 3:
    print('[Obsidian-html]')
    print('- Convert obsidian to html: \n\tpython run.py <path to obsidian notes> <path to entrypoint>\n')
    print('- Convert md to html: \n\tpython run.py <path to md files> <path to md entrypoint> -md\n')
    print('- Add -v for verbose output')
    print('- Add -h to get helptext')
    print('- Add -nc to skip erasing output folders')
    print('- Add -md to convert proper markdown to html (entrypoint and root_folder path should point to proper markdown sources)')
    exit()

if '-v' in sys.argv:
    verbose_printout = True

if '-nc' in sys.argv:
    no_clean = True

root_folder_path = Path(sys.argv[1]).resolve()   # first folder that contains all markdown files
entrypoint_path = Path(sys.argv[2]).resolve()    # The note that will be used as the index.html
md_folder_path = Path(sys.argv[3]).resolve()
html_output_folder_path = Path(sys.argv[4]).resolve()
site_name = sys.argv[5]
html_url_prefix = sys.argv[6].replace("'", '')

# Paths
md_to_html_entrypoint_path = md_folder_path.joinpath('index.md').resolve()
rel_entrypoint_path = entrypoint_path.relative_to(root_folder_path)

if '-md' in sys.argv:
    toggle_compile_md = False
    md_folder_path = root_folder_path
    md_to_html_entrypoint_path = entrypoint_path


# Preprocess
# ------------------------------------------
# Remove previous output
if no_clean == False:
    print('> CLEARING OUTPUT FOLDERS')
    if toggle_compile_md:
        if md_folder_path.exists():
            shutil.rmtree(md_folder_path)

    if html_output_folder_path.exists():
        shutil.rmtree(html_output_folder_path)    

# Recreate tree
print('> CREATING OUTPUT FOLDERS')
md_folder_path.mkdir(parents=True, exist_ok=True)
html_output_folder_path.mkdir(parents=True, exist_ok=True)


# Convert Obsidian to markdown
# ------------------------------------------
# Load all filenames in the root folder.
# This data will be used to check which files are local, and to get their full path
# It's clear that no two files can be allowed to have the same file name.
if toggle_compile_md:
    files = {}
    for path in root_folder_path.rglob('*'):
        if path.name in files.keys() and allow_duplicate_filenames_in_root == False:
            raise DuplicateFileNameInRoot(f"Two or more files with the name \"{path.name}\" exist in the root folder. See {str(path)} and {files[path.name]['fullpath']}.")

        files[path.name] = {'fullpath': str(path), 'processed': False}  


    # Start conversion with entrypoint.
    # Note: this will mean that any note not (indirectly) linked by the entrypoint will not be included in the output!
    print(f'> COMPILING MARKDOWN FROM OBSIDIAN CODE ({str(entrypoint_path)})')
    recurseObisidianToMarkdown(str(entrypoint_path))


# Convert Markdown to Html
# ------------------------------------------
if toggle_compile_html:
    print(f'> COMPILING HTML FROM MARKDOWN CODE ({str(md_to_html_entrypoint_path)})')

    # Get html template code. Every note will become a html page, where the body comes from the note's 
    # markdown, and the wrapper code from this template.
    with open('src/template.html') as f:
        html_template = f.read()

    # Load all filenames in the markdown folder
    # This data is used to check which links are local
    files = {}
    for path in Path(md_folder_path).rglob('*'):
        rel_path_posix = path.relative_to(md_folder_path).as_posix()
        files[rel_path_posix] = {'fullpath': str(path.resolve()), 'processed': False}  

    # Start conversion from the entrypoint
    ConvertMarkdownPageToHtmlPage(str(md_to_html_entrypoint_path))

    # Add Extra stuff to the output directories
    # ------------------------------------------
    os.makedirs(html_output_folder_path.joinpath('static'), exist_ok=True)
    shutil.copyfile('src/main.css', html_output_folder_path.joinpath('main.css'))
    shutil.copyfile('src/external.svg', html_output_folder_path.joinpath('external.svg'))
    shutil.copyfile('src/fonts/SourceCodePro-Regular.ttf', html_output_folder_path.joinpath('static/SourceCodePro-Regular.ttf'))

    with open('src/not_created.html') as f :
        with open (html_output_folder_path.joinpath('not_created.html'), 'w', encoding="utf-8") as t:
            t.write(html_template.replace('{content}', f.read()))

print('> DONE')