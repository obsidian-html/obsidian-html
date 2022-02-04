import sys                  # commandline arguments
import os                   #
import shutil               # used to remove a non-empty directory, copy files
import re                   # regex string finding/replacing
from pathlib import Path    # 
import markdown             # convert markdown to html
import yaml
import urllib.parse         # convert link characters like %
import frontmatter

from .MarkdownPage import MarkdownPage
from .MarkdownLink import MarkdownLink
from .lib import DuplicateFileNameInRoot, GetObsidianFilePath, image_suffixes
from .PicknickBasket import PicknickBasket

# Open source files in the package
import importlib.resources as pkg_resources
import importlib.util
from . import src 

def OpenIncludedFile(resource):
    path = importlib.util.find_spec("obsidianhtml.src").submodule_search_locations[0]
    path = os.path.join(path, resource)
    with open(path, 'r', encoding="utf-8") as f:
        return f.read()

def OpenIncludedFileBinary(resource):
    path = importlib.util.find_spec("obsidianhtml.src").submodule_search_locations[0]
    path = os.path.join(path, resource)
    with open(path, 'rb') as f:
        return f.read()        


# python run.py 'C:\Users\Installer\OneDrive\Obsidian\Notes' "C:\Users\Installer\OneDrive\Obsidian\Notes\Devfruits Notes.md" "output/md" "output/html" "Devfruits/Notes"

def recurseObisidianToMarkdown(page_path_str, pb):
    paths = pb.paths
    files = pb.files
    conf = pb.config

    # Convert path string to Path and do a double check
    page_path = Path(page_path_str).resolve()
    if page_path.exists() == False:
        return
    if page_path.suffix != '.md':
        return

    md = MarkdownPage(page_path, paths['obsidian_folder'], files)
    md.ConvertObsidianPageToMarkdownPage(paths['md_folder'], paths['obsidian_entrypoint'])

    # Add yaml frontmatter back in
    md.page = (frontmatter.dumps(frontmatter.Post("", **md.metadata))) + '\n' + md.page

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
        if conf['toggles']['verbose_printout']:
            print(f"converting {files[link_path]['fullpath']} (parent {page_path})")
        recurseObisidianToMarkdown(files[link_path]['fullpath'], pb)

def ConvertMarkdownPageToHtmlPage(page_path_str, pb):
    page_path = Path(page_path_str).resolve()
    paths = pb.paths
    files = pb.files
    html_template = pb.html_template
    conf = pb.config

    if page_path.exists() == False:
        return
    if page_path.suffix != '.md':
        return

    # Load contents 
    md = MarkdownPage(page_path, paths['md_folder'], files)
    md.SetDestinationPath(paths['html_output_folder'], paths['md_entrypoint'])

    # [1] Replace code blocks with placeholders so they aren't altered
    # They will be restored at the end
    md.StripCodeSections()     

    # Get all markdown links. 
    # This is any string in between '](' and  ')'
    proper_links = re.findall("(?<=\]\().+?(?=\))", md.page)
    for l in proper_links:
        # Init link
        link = MarkdownLink(l, page_path, paths['md_folder'], url_unquote=True, relative_path_md = conf['toggles']['relative_path_md'])

        # Don't process in the following cases
        if link.isValid == False or link.isExternal == True: 
            continue

        isMd = False
        filename = link.src_path.name
        if filename[-3:] == '.md':
            isMd = True
        if Path(filename).suffix == '':
            isMd = True
            filename += '.md'

        # [12] Copy non md files over wholesale, then we're done for that kind of file
        if link.suffix != '.md' and link.suffix not in image_suffixes:
            paths['html_output_folder'].joinpath(link.rel_src_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(link.src_path, paths['html_output_folder'].joinpath(link.rel_src_path))
            continue

        # [13] Link to a custom 404 page when linked to a not-created note
        if link.url.split('/')[-1] == 'not_created.md':
            new_link = '](/not_created.html)'
        else:
            if link.rel_src_path_posix not in files.keys():
                continue

            md.links.append(link.rel_src_path_posix)

            # [11.1] Rewrite .md links to .html (when the link is to a file in our root folder)
            query_part = ''
            if link.query != '':
                query_part = link.query_delimiter + link.query 
            new_link = f']({conf["html_url_prefix"]}/{link.rel_src_path_posix[:-3]}.html{query_part})'
            
        # Update link
        safe_link = re.escape(']('+l+')')
        md.page = re.sub(safe_link, new_link, md.page)

    # [4] Handle local image links (copy them over to output)
    # ----
    for link in re.findall("(?<=\!\[\]\()(.*?)(?=\))", md.page):
        l = urllib.parse.unquote(link)
        full_link_path = page_path.parent.joinpath(l).resolve()
        rel_path = full_link_path.relative_to(paths['md_folder'])

        # Only handle local image files (images located in the root folder)
        # Doublecheck, who knows what some weird '../../folder/..' does...
        if rel_path.as_posix() not in files.keys():
            if conf['toggles']['warn_on_skipped_image']:
                warnings.warn(f"Image {str(full_link_path)} treated as external and not imported in html")            
            continue

        # Copy src to dst
        dst_path = paths['html_output_folder'].joinpath(rel_path)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(full_link_path, dst_path)

        # [11.2] Adjust image link in page to new dst folder (when the link is to a file in our root folder)
        new_link = '![]('+urllib.parse.quote(rel_path.as_posix())+')'
        safe_link = re.escape('![](/'+link+')')
        md.page = re.sub(safe_link, new_link, md.page)
   

    # [1] Restore codeblocks/-lines
    # ----
    md.RestoreCodeSections()

    # [11] Convert markdown to html
    # ----
    extension_configs = {
    'codehilite ': {
        'linenums': True
    }}
    html_body = markdown.markdown(md.page, extensions=['extra', 'codehilite', 'toc', 'md_mermaid'], extension_configs=extension_configs)

    # [14] Tag external links with a class so it can be decorated differently
    for l in re.findall(r'(?<=\<a href=")([^"]*)', html_body):
        if l == '':
            continue
        if l[0] == '/':
            # Internal link, skip
            continue

        new_str = f"<a href=\"{l}\" class=\"external-link\""
        safe_str = f"<a href=\"{l}\""
        html_body = html_body.replace(safe_str, new_str)

    # [15] Tag not created links with a class so it can be decorated differently
    html_body = html_body.replace('<a href="/not_created.html">', '<a href="/not_created.html" class="nonexistent-link">')

    # [16] Wrap body html in valid html structure from template
    html = html_template.replace('{content}', html_body).replace('{title}', conf['site_name']).replace('{html_url_prefix}', conf['html_url_prefix'])

    # Save file
    # ---- 
    md.dst_path.parent.mkdir(parents=True, exist_ok=True)   
    html_dst_path_posix = md.dst_path.as_posix()[:-3] + '.html' 

    md.AddToTagtree(pb.tagtree, md.dst_path.relative_to(paths['html_output_folder']).as_posix()[:-3] + '.html')

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
        if conf['toggles']['verbose_printout']:
            print("html: converting ", files[link_path]['fullpath'], " (parent ", md.src_path, ")")

        ConvertMarkdownPageToHtmlPage(files[link_path]['fullpath'], pb)  

def recurseTagList(tagtree, tagpath, pb):
    html_url_prefix = pb.config['html_url_prefix']
    tag_dst_path = pb.paths['html_output_folder'].joinpath(f'{tagpath}index.html').resolve()
    tag_dst_path_posix = tag_dst_path.as_posix()
    rel_dst_path_as_posix = tag_dst_path.relative_to(pb.paths['html_output_folder']).as_posix()

    # Compile markdown
    md = ''
    if len(tagtree['subtags'].keys()) > 0:
        md += '# Subtags\n'
        for key in tagtree['subtags'].keys():
            rel_key_path_as_posix = recurseTagList(tagtree['subtags'][key], tagpath + key + '/', pb)
            md += f'- [{key}](/{rel_key_path_as_posix})' + '\n'

    if len(tagtree['notes']) > 0:
        md = '\n# Notes\n'
        for note in tagtree['notes']:
            md += f'- [{note.replace(".html", "")}]({html_url_prefix}/{note})\n'

    # Compile html
    html_body = markdown.markdown(md, extensions=['extra', 'codehilite', 'toc', 'md_mermaid'])
    html_body = html_body.replace('<a href="/not_created.html">', '<a href="/not_created.html" class="nonexistent-link">')
    html = pb.html_template.replace('{content}', html_body).replace('{title}', pb.config['site_name']).replace('{html_url_prefix}', pb.config['html_url_prefix'])

    # Write file
    tag_dst_path.parent.mkdir(parents=True, exist_ok=True)   
    with open(tag_dst_path_posix, 'w', encoding="utf-8") as f:
        f.write(html) 

    return rel_dst_path_as_posix

def main():
    # Config
    # ------------------------------------------
    if '-h' in sys.argv or len(sys.argv) < 3:
        print('[Obsidian-html]')
        print('- Add -i </path/to/input.yml> to provide config')
        print('- Add -v for verbose output')
        print('- Add -h to get helptext')
        print('- Add -eht <target/path/file.name> to export the html template.')
        exit()

    # Functions other than main function
    export_html_template_target_path = None
    for i, v in enumerate(sys.argv):
        if v == '-eht':
            if len(sys.argv) < (i + 2):
                raise Exception("No output path given.\n Use obsidianhtml -eht /target/path/to/template.html to provide input.")
                exit(1)
            export_html_template_target_path = Path(sys.argv[i+1]).resolve()
            export_html_template_target_path.parent.mkdir(parents=True, exist_ok=True)
            html = OpenIncludedFile('template.html')
            with open (export_html_template_target_path, 'w', encoding="utf-8") as t:
                t.write(html)
            print(f"Exported html template to {str(export_html_template_target_path)}.")
            exit(0)

    # Load input yaml
    input_yml_path_str = ''
    for i, v in enumerate(sys.argv):
        if v == '-i':
            input_yml_path_str = sys.argv[i+1]
            break

    if input_yml_path_str == '':
        raise Exception("No yaml input given.\n Use obsidianhtml -i /path/to/config.yml to provide input.")
        exit(1)

    with open(input_yml_path_str, 'rb') as f:
        conf = yaml.load(f.read(), Loader=yaml.SafeLoader) 

    # Overwrite conf
    for i, v in enumerate(sys.argv):
        if v == '-v':
            conf['toggles']['verbose_printout'] = True

    # Input
    # ------------------------------------------
    # Set Paths
    paths = {
        'obsidian_folder': Path(conf['obsidian_folder_path_str']).resolve(),
        'md_folder': Path(conf['md_folder_path_str']).resolve(),
        'obsidian_entrypoint': Path(conf['obsidian_entrypoint_path_str']).resolve(),
        'md_entrypoint': Path(conf['md_entrypoint_path_str']).resolve(),
        'html_output_folder': Path(conf['html_output_folder_path_str']).resolve()
    }

    # Deduce relative paths
    paths['rel_obsidian_entrypoint'] = paths['obsidian_entrypoint'].relative_to(paths['obsidian_folder'])
    paths['rel_md_entrypoint_path']  = paths['md_entrypoint'].relative_to(paths['md_folder'])

    #print(yaml.dump(conf, allow_unicode=True, default_flow_style=False))

    # Preprocess
    # ------------------------------------------
    # Remove previous output
    if conf['toggles']['no_clean'] == False:
        print('> CLEARING OUTPUT FOLDERS')
        if conf['toggles']['compile_md']:
            if paths['md_folder'].exists():
                shutil.rmtree(paths['md_folder'])

        if paths['html_output_folder'].exists():
            shutil.rmtree(paths['html_output_folder'])    

    # Recreate tree
    print('> CREATING OUTPUT FOLDERS')
    paths['md_folder'].mkdir(parents=True, exist_ok=True)
    paths['html_output_folder'].mkdir(parents=True, exist_ok=True)

    # Make "global" object that we can pass so functions
    pb = PicknickBasket(conf, paths)

    # Convert Obsidian to markdown
    # ------------------------------------------
    # Load all filenames in the root folder.
    # This data will be used to check which files are local, and to get their full path
    # It's clear that no two files can be allowed to have the same file name.
    if conf['toggles']['compile_md']:
        files = {}
        for path in paths['obsidian_folder'].rglob('*'):
            if path.is_dir():
                continue
            if path.resolve().is_relative_to(paths['obsidian_folder'].joinpath('.obsidian')):
                continue
            if path.name in files.keys() and conf['toggles']['allow_duplicate_filenames_in_root'] == False:
                print(path)
                raise DuplicateFileNameInRoot(f"Two or more files with the name \"{path.name}\" exist in the root folder. See {str(path)} and {files[path.name]['fullpath']}.")

            files[path.name] = {'fullpath': str(path), 'processed': False}  

        pb.files = files

        # Start conversion with entrypoint.
        # Note: this will mean that any note not (indirectly) linked by the entrypoint will not be included in the output!
        print(f'> COMPILING MARKDOWN FROM OBSIDIAN CODE ({str(paths["obsidian_entrypoint"])})')
        recurseObisidianToMarkdown(str(paths['obsidian_entrypoint']), pb)


    # Convert Markdown to Html
    # ------------------------------------------
    if conf['toggles']['compile_html']:
        print(f'> COMPILING HTML FROM MARKDOWN CODE ({str(paths["md_entrypoint"])})')

        # Get html template code. Every note will become a html page, where the body comes from the note's 
        # markdown, and the wrapper code from this template.
        if  'html_template_path_str' in conf.keys() and conf['html_template_path_str'] != '':
            print('-------------')
            with open(Path(conf['html_template_path_str']).resolve()) as f:
                html_template = f.read()
        else:
            html_template = OpenIncludedFile('template.html')

        if '{content}' not in html_template:
            raise Exception('The provided html template does not contain the string `{content}`. This will break its intended use as a template.')
            exit(1)

        # Load all filenames in the markdown folder
        # This data is used to check which links are local
        files = {}
        for path in paths['md_folder'].rglob('*'):
            rel_path_posix = path.relative_to(paths['md_folder']).as_posix()
            files[rel_path_posix] = {'fullpath': str(path.resolve()), 'processed': False}  

        pb.files = files
        pb.html_template = html_template

        # Start conversion from the entrypoint
        ConvertMarkdownPageToHtmlPage(str(paths['md_entrypoint']), pb)

        # Create tag page
        recurseTagList(pb.tagtree, 'tags/', pb)

        # Add Extra stuff to the output directories
        # ------------------------------------------
        os.makedirs(paths['html_output_folder'].joinpath('static'), exist_ok=True)

        css = OpenIncludedFile('main.css')
        with open (paths['html_output_folder'].joinpath('main.css'), 'w', encoding="utf-8") as t:
            t.write(css)
        mermaidcss = OpenIncludedFile('mermaid.css')
        with open (paths['html_output_folder'].joinpath('mermaid.css'), 'w', encoding="utf-8") as t:
            t.write(mermaidcss)
        mermaidjs = OpenIncludedFile('mermaid.min.js')
        with open (paths['html_output_folder'].joinpath('mermaid.min.js'), 'w', encoding="utf-8") as t:
            t.write(mermaidjs)
        svg = OpenIncludedFile('external.svg')
        with open (paths['html_output_folder'].joinpath('external.svg'), 'w', encoding="utf-8") as t:
            t.write(svg)
        scp = OpenIncludedFileBinary('SourceCodePro-Regular.ttf')
        with open (paths['html_output_folder'].joinpath('static/SourceCodePro-Regular.ttf'), 'wb') as t:
            t.write(scp)                    
        nc = OpenIncludedFile('not_created.html')
        with open (paths['html_output_folder'].joinpath('not_created.html'), 'w', encoding="utf-8") as t:
            t.write(html_template.replace('{content}', nc))

    print('> DONE')
