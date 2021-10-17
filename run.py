import sys                  # commandline arguments
import os                   #
import shutil               # used to remove a non-empty directory, copy files
import re                   # regex string finding/replacing
from pathlib import Path    # 
import markdown             # convert markdown to html
import urllib.parse         # convert link characters like %
from lib import MarkdownPage, MarkdownLink, DuplicateFileNameInRoot, GetObsidianFilePath, image_suffixes

# python run.py 'C:\Users\Installer\OneDrive\Obsidian\Notes' "C:\Users\Installer\OneDrive\Obsidian\Notes\Devfruits Notes.md" "output/md" "output/html" "Devfruits/Notes"

def recurseObisidianToMarkdown(page_path_str):
    # Convert path string to Path and do a double check
    page_path = Path(page_path_str).resolve()
    if page_path.exists() == False:
        return
    if page_path.suffix != '.md':
        return

    md = MarkdownPage(page_path, root_folder_path, files)
    md.ConvertObsidianPageToMarkdownPage(md_folder_path, entrypoint_path)

    # -- Save file
    # Create folder if necessary
    md.dst_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write markdown
    with open(md.dst_path, 'w', encoding="utf-8") as f:
        f.write(md.page)

    # -- Recurse for every link in the current page
    for l in md.links:
        link = GetObsidianFilePath(l, files)
        if link[1] == False or link[1]['processed'] == True:
            continue
        link_path = link[0]

        # Mark the file as processed so that it will not be processed again at a later stage
        files[link_path]['processed'] = True         

        # Convert the note that is linked to
        if verbose_printout:
            print(f"converting {files[link_path]['fullpath']} (parent {page_path})")
        recurseObisidianToMarkdown(files[link_path]['fullpath'])

def ConvertMarkdownPageToHtmlPage(page_path_str):
    page_path = Path(page_path_str).resolve()

    if page_path.exists() == False:
        return
    if page_path.suffix != '.md':
        return

    # Load contents 
    md = MarkdownPage(page_path, md_folder_path, files)
    md.SetDestinationPath(html_output_folder_path, md_to_html_entrypoint_path)

    # Replace code blocks with placeholders so they aren't altered
    # They will be restored at the end
    md.StripCodeSections()     

    # Get all markdown links. 
    # This is any string in between '](' and  ')'
    proper_links = re.findall("(?<=\]\().+?(?=\))", md.page)
    for l in proper_links:
        # Init link
        link = MarkdownLink(l, page_path, md_folder_path, url_unquote=True, relative_path_md = relative_path_md)

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