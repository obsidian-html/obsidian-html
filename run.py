import sys
import re
from pathlib import Path
import frontmatter
import markdown
 

# python run.py 'C:\Users\Installer\OneDrive\Obsidian\Notes' 'C:\Users\Installer\OneDrive\Obsidian\Notes\Work.md'


root_folder = sys.argv[1]
entrypoint = sys.argv[2]

# Load all filenames in the root folder
files = {}
for path in Path(root_folder).rglob('*.md'):
    p = str(path)
    files[path.name] = {'fullpath': p, 'processed': False}

# Get html template code
with open('src/template.html') as f:
    html_template = f.read()


# Process single page
# ------------------------------------------
def ConvertPage(page_path):
    # Load contents of entrypoint and strip frontmatter (frontmatter is loaded into dict keys)
    if Path(page_path).exists() == False:
        return

    page = frontmatter.load(page_path)

    # Get obsidian links
    links = re.findall("(?<=\[\[).+?(?=\])", page.content)

    # Replace links with proper markdown
    for l in links:
        # A link in Obsidian can have the format 'filename|alias'
        parts = l.split('|')
        filename = parts[0].split('/')[-1]
        alias = filename
        if len(parts) > 1:
            alias = parts[1]

        if filename+'.md' not in files.keys():
            url_path = 'not_created.md'
        else:
            full_path = files[filename+'.md']['fullpath']

            # Convert filepath to url relative path
            if (full_path == entrypoint):
                # Replace any links pointing to the entrypoint to point to '/index.html'
                url_path = '/'
            else:
                url_path = full_path.replace(root_folder+'\\', '').replace('\\', '/').replace(' ', '%20')

        # Insert new link
        page.content = page.content.replace('[['+l+']]', f"[{alias}](/{url_path})")

    # Fix newline issue
    page.content = page.content.replace("\n", "   \n")

    # Insert markdown links for http(s) links
    bare_links = re.findall("(?<![\[\(])(http.[^\s]*)", page.content)

    for l in bare_links:
        new = f"[{l}]({l})"
        safe_link = re.escape(l)
        page.content = re.sub(f"(?<![\[\(])({safe_link})", new, page.content)

    # Save file
    if page_path == entrypoint:
        filepath =  Path('output/md/index.md')
        html_fp = Path('output/html/index.html')
    else:
        target = page_path.replace(root_folder, '').replace('\\', '/')
        filepath = Path('output/md/'+target)
        html_fp = Path('output/html/'+target.replace('.md', '.html'))

    folderpath = filepath.parent
    folderpath.mkdir(parents=True, exist_ok=True) # create dir structure if needed

    folderpath = html_fp.parent
    folderpath.mkdir(parents=True, exist_ok=True) # create dir structure if needed    

    # Write markdown
    with open(filepath, 'w') as f:
        f.write(page.content)

    # Write html
    with open(html_fp, 'w') as f:
        html = html_template.replace('{content}', markdown.markdown(page.content, extensions=['extra']).replace('.md">', '.html">'))
        f.write(html)    
    
    
    # Recurse for every link
    for l in links:
        link_path = l.split('|')[0].split('/')[-1]+'.md'
        
        if link_path not in files.keys():
            continue

        if files[link_path]['processed'] == True:
            continue

        files[link_path]['processed'] = True         
        print(f"converting {files[link_path]['fullpath']} (parent {page_path})")

        ConvertPage(files[link_path]['fullpath'])

ConvertPage(entrypoint)

# Extra stuff
with open('src/main.css') as f :
    with open ('output/html/main.css', 'w') as t:
        t.write(f.read())

with open('src/not_created.html') as f :
    with open ('output/html/not_created.html', 'w') as t:
        t.write(html_template.replace('{content}', f.read()))
