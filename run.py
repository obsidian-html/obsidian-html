import sys                  # commandline arguments
import re                   # regex string finding/replacing
from pathlib import Path    # 
import frontmatter          # remove yaml frontmatter from md files
import markdown             # convert markdown to html
 
# python run.py 'C:\Users\Installer\OneDrive\Obsidian\Notes' 'C:\Users\Installer\OneDrive\Obsidian\Notes\Work.md'

# Input
# ------------------------------------------
root_folder = sys.argv[1]   # first folder that contains all markdown files
entrypoint = sys.argv[2]    # The note that will be used as the index.html

# Preprocess
# ------------------------------------------
# Load all filenames in the root folder.
# This data will be used to convert implicit Obsidian links to proper markdown links. 
files = {}
for path in Path(root_folder).rglob('*.md'):
    files[path.name] = {'fullpath': str(path), 'processed': False}  
    # ^ the 'processed' switch helps us to avoid infinite loops

# Get html template code. Every note will become a html page, where the body comes from the note's 
# markdown, and the wrapper code from this template.
with open('src/template.html') as f:
    html_template = f.read()


def ConvertPage(page_path):
    # ^ This function creates a proper markdown version of the Obsidian note, 
    #   an html page, and it will recursively call itself on any links in the note.

    # Links can be made in Obsidian without creating the note. 
    # In this case we don't have to do anything.
    if Path(page_path).exists() == False:
        return

    # Load contents of entrypoint and strip frontmatter yaml.
    # If the frontmatter needs to be used at a later date: the frontmatter is loaded into dict keys, 
    # e.g. page['tags']
    page = frontmatter.load(page_path)

    # Get obsidian links. 
    # This is any string in between [[ and ]], e.g. [[My Note]]
    links = re.findall("(?<=\[\[).+?(?=\])", page.content)

    # Replace Obsidian links with proper markdown
    for l in links:
        # A link in Obsidian can have the format 'filename|alias'
        parts = l.split('|')
        filename = parts[0].split('/')[-1]
        alias = filename
        if len(parts) > 1:
            alias = parts[1]

        # Links can be made in Obsidian without creating the note.
        # When we link to a nonexistant note, link to the not_created.md placeholder instead.
        if filename+'.md' not in files.keys():
            relative_path = '/not_created.md'
        else:
            # Obtain the full path of the file in the directory tree
            # e.g. 'C:\Users\Installer\OneDrive\Obsidian\Notes\Work\Harbor Docs.md'
            full_path = files[filename+'.md']['fullpath']

            # Replace any links pointing to the entrypoint to point to '/index.html'
            if (full_path == entrypoint):
                relative_path = '/index.md'
            else:
                # Convert full Windows(!) path to url link, e.g: 
                # 'C:\Users\Installer\OneDrive\Obsidian\Notes\Work\Harbor Docs.md' --> .replace(root_folder, '') -->
                # '\Work\Harbor Docs.md' --> .replace('\\', '/') -->
                # '/Work/Harbor Docs.md' 
                relative_path = full_path.replace(root_folder, '').replace('\\', '/')

        # Replace Obsidian link with proper markdown link
        url_path = relative_path.replace(' ', '%20')
        page.content = page.content.replace('[['+l+']]', f"[{alias}]({url_path})")

    # Fix newline issue by adding three spaces before any newline
    page.content = page.content.replace("\n", "   \n")

    # Insert markdown links for bare http(s) links (those without the [name](link) format).
    for l in re.findall("(?<![\[\(])(http.[^\s]*)", page.content):
        new_md_link = f"[{l}]({l})"
        safe_link = re.escape(l)
        page.content = re.sub(f"(?<![\[\(])({safe_link})", new_md_link, page.content)

    # Save file
    md_filepath = Path('output/md' + relative_path)
    html_filepath = Path('output/html' + relative_path.replace('.md', '.html'))
    
    folderpath = md_filepath.parent
    folderpath.mkdir(parents=True, exist_ok=True) # create dir structure if needed
    folderpath = html_filepath.parent
    folderpath.mkdir(parents=True, exist_ok=True) # create dir structure if needed    

    # Write markdown
    with open(md_filepath, 'w') as f:
        f.write(page.content)

    # Write html
    with open(html_filepath, 'w') as f:
        # Convert markdown to html
        html_body = markdown.markdown(page.content, extensions=['extra'])
        # change links to xxx.md to xxx.html 
        html_body = html_body.replace('.md">', '.html">')
        # Wrap body html in valid html structure from template
        html = html_template.replace('{content}', html_body)
        f.write(html)    
    
    # Recurse for every link in the current page
    for l in links:
        # Remove possible alias suffix, folder prefix, and add '.md' to get a valid lookup key
        link_path = l.split('|')[0].split('/')[-1]+'.md'
        
        # Skip non-existent notes and notes that have been processed already
        if link_path not in files.keys():
            continue
        if files[link_path]['processed'] == True:
            continue

        # Mark the file as processed so that it will not be processed again at a later stage
        files[link_path]['processed'] = True         

        # Convert the note that is linked to
        print(f"converting {files[link_path]['fullpath']} (parent {page_path})")
        ConvertPage(files[link_path]['fullpath'])

# Convert files
# ------------------------------------------
# Start conversion with entrypoint.
# Note: this will mean that any note not (indirectly) linked by the entrypoint will not be included in the output!
ConvertPage(entrypoint)

# Add Extra stuff to the output directories
# ------------------------------------------
with open('src/main.css') as f :
    with open ('output/html/main.css', 'w') as t:
        t.write(f.read())

with open('src/not_created.html') as f :
    with open ('output/html/not_created.html', 'w') as t:
        t.write(html_template.replace('{content}', f.read()))
