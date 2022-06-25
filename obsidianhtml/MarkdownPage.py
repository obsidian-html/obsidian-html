from __future__ import annotations
import re                   # regex string finding/replacing
from pathlib import Path    # 
import frontmatter          # remove yaml frontmatter from md files
import urllib.parse         # convert link characters like %
import warnings
from .lib import DuplicateFileNameInRoot, GetObsidianFilePath, ConvertTitleToMarkdownId, MalformedTags, OpenIncludedFile
from .HeaderTree import PrintHeaderTree, ConvertMarkdownToHeaderTree
from .FileFinder import FindFile

class MarkdownPage:
    page = None             # Pure markdown code read from src file
    yaml = None             # Yaml is stripped from the src file and saved here
    codeblocks = None       # used to safely store ```codeblock content
    codelines = None        # Used to safely store `codeline` content
    links = None            # Used to recurse to any page linked to by this page

    src_path  = None        # Path() object of src file
    rel_src_path  = None    # Path() object relative to given markdown root folder (src_folder_path)
    src_folder_path = None  # Path() object of given obsidian root folder
    dst_folder_path = None  # Path() object of given markdown output folder
    dst_path = None         # Path() object of destination file

    isEntryPoint = False

    file_tree = None        # Tree of files that are found in the root folder

    def __init__(self, pb, fo:'OH_File', input_type, file_tree):
        self.pb = pb
        self.fo = fo
        self.file_tree = file_tree
        
        # remove?
        self.src_path = fo.path[input_type]['file_absolute_path']
        self.src_folder_path = fo.path[input_type]['folder_path']
        self.rel_src_path = fo.path[input_type]['file_relative_path']
        self.input_type = input_type

        self.links = []
        self.codeblocks = []
        self.codelines = []
        
        # Load contents of entrypoint and strip frontmatter yaml.
        with open(self.src_path, encoding="utf-8") as f:
            self.metadata, self.page = frontmatter.parse(f.read())

    def StripCodeSections(self):
        """(Temporarily) Remove codeblocks/-lines so that they are not altered in all the conversions. Placeholders are inserted."""
        self.codeblocks = re.findall("^```([\s\S]*?)```[\s]*?$", self.page, re.MULTILINE)
        for i, match in enumerate(self.codeblocks):
            self.page = self.page.replace("```"+match+"```", f'%%%codeblock-placeholder-{i}%%%')
            
        self.codelines = re.findall("`(.*?)`", self.page)
        for i, match in enumerate(self.codelines):
            self.page = self.page.replace("`"+match+"`", f'%%%codeline-placeholder-{i}%%%')
           
    def RestoreCodeSections(self):
        """Undo the action of StripCodeSections."""
        for i, value in enumerate(self.codeblocks):
            self.page = self.page.replace(f'%%%codeblock-placeholder-{i}%%%', f"```{value}```\n")
        for i, value in enumerate(self.codelines):
            self.page = self.page.replace(f'%%%codeline-placeholder-{i}%%%', f"`{value}`")  

    def add_tag(self, tag):
        if 'tags' not in self.metadata:
            self.metadata['tags'] = []
        self.metadata['tags'].append(tag)
    
    def AddToTagtree(self, tagtree, url=''):
        if 'tags' not in self.metadata:
            return

        if url == '':
            url = self.fo.get_link('html')

        for tag in self.metadata['tags']:
            if (not isinstance(tag, str)):
                raise MalformedTags(f"Tag {tag} in frontmatter of \"{self.src_path}\" is of type {type(tag)}, but should be a string. (Items under 'tags:' can not include a ':' on its line).")

        for tag in self.metadata['tags']:
            ctagtree = tagtree
            for n, subtag in enumerate(tag.split('/')):
                if subtag not in ctagtree['subtags'].keys():
                    ctagtree['subtags'][subtag] = {'notes': [], 'subtags': {}}
                ctagtree = ctagtree['subtags'][subtag]

                if n == (len(tag.split('/')) - 1):
                    ctagtree['notes'].append(url)

    def GetVideoHTML(self, file_name, relative_path_corrected, suffix):
        mime_type_lut = {
            'mp4': 'video/mp4',
            'webm': 'video/webm',
            'flv': 'video/x-flv',
            '3gp': 'video/3gpp',
            'mov': 'video/quicktime',
            'wmv': 'video/x-ms-wmv',
            'avi': 'video/x-msvideo'
        }
        try:
            mime_type = mime_type_lut[suffix]
        except:
            mime_type = ''
        video_template = OpenIncludedFile('html/templates/video_template.html')
        return video_template.replace('{url}', relative_path_corrected).replace('{mime_type}', mime_type)

    def GetAudioHTML(self, file_name, relative_path_corrected, suffix):
        mime_type_lut = {
            'mp3': 'audio/mpeg',
            'm4a': 'audio/mp4',
            'wav': 'audio/x-wav'
        }
        try:
            mime_type = mime_type_lut[suffix]
        except:
            mime_type = ''
        audio_template = OpenIncludedFile('html/templates/audio_template.html')
        return audio_template.replace('{url}', relative_path_corrected).replace('{mime_type}', mime_type)

    def ConvertObsidianPageToMarkdownPage(self, origin:'OH_file'=None, include_depth=0, includer_page_depth=None):
        """Full subroutine converting the Obsidian Code to proper markdown. Linked files are copied over to the destination folder."""

        # -- Set origin (calling page), this will always be self.fo unless origin is passed in
        if origin is None:
            origin = self.fo 
        
        # -- Get page depth
        page_folder_depth = self.fo.metadata['depth']

        if includer_page_depth is not None:
            page_folder_depth = includer_page_depth
            # overwrite
            if self.fo.metadata['is_entrypoint']:
                page_folder_depth = 0

        # -- [1] Replace code blocks with placeholders so they aren't altered
        # They will be restored at the end
        self.StripCodeSections() 

        # -- [2] Add newline between paragraph and lists
        buffer = ''
        prev_is_list_line = False
        for i, line in enumerate(self.page.split('\n')):
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
        self.page = buffer

        # -- [?] Remove whitespace in front of header hashtags
        self.page = re.sub('(^\ [\ ]*)(?=#)', '', self.page, flags=re.MULTILINE)

        # -- [3] Convert Obsidian type img links to proper md image links
        # Further conversion will be done in the block below
        for link in re.findall("(?<=\!\[\[)(.*?)(?=\])", self.page):
            new_link = '![]('+link+')'

            # Obsidian page inclusions use the same tag...
            # Skip if we don't match image suffixes. Inclusions are handled at the end.
            if len(link.split('.')) == 1 or link.split('.')[-1].split('|')[0] not in self.pb.gc('included_file_suffixes', cached=True):
                new_link = f'<inclusion href="{link}" />'

            safe_link = re.escape('![['+link+']]')
            self.page = re.sub(safe_link, new_link, self.page)

        # -- [4] Handle local image/video/audio links (copy them over to output)
        for link in re.findall("(?<=\!\[\]\()(.*?)(?=\))", self.page):
            #clean_link_name = urllib.parse.unquote(link).split('/')[-1].split('|')[0]
            clean_link = urllib.parse.unquote(link).split('|')[0]

            # Find file
            rel_path_str, lo = FindFile(self.pb.files, clean_link, self.pb)
            if rel_path_str == False:
                if self.pb.gc('toggles/verbose_printout', cached=True):
                    print(f"\t\tImage/file with obsidian link of '{clean_link}' (original {link}) will not be copied over in this step.")
                    if '://' in link:
                        print("\t\t\t<continued> The link seems to be external (contains ://)")
                    else:
                        print(f"\t\t\t<continued> The link was not found in the file tree. Clean links in the file tree are: {', '.join(self.file_tree.keys())}")
                continue

            # Get shorthand info
            suffix = lo.path['note']['suffix']
            relative_path = lo.path['markdown']['file_relative_path']

            # Copy file over to markdown destination
            lo.copy_file('ntm')

            # Adjust link in page
            file_name = urllib.parse.unquote(link)
            relative_path = relative_path.as_posix()
            relative_path = ('../' * page_folder_depth) + relative_path
            new_link = '![]('+urllib.parse.quote(relative_path)+')'

            # Handle video/audio usecase
            if lo.metadata['is_video']:
                new_link = self.GetVideoHTML(file_name, relative_path, suffix)
            if lo.metadata['is_audio']:
                new_link = self.GetAudioHTML(file_name, relative_path, suffix)
            
            safe_link = re.escape('![]('+link+')')
            self.page = re.sub(safe_link, new_link, self.page)

        # -- [5] Change file name in proper markdown links to path
        # And while we are busy, change the path to point to the full relative path
        proper_links = re.findall("(?<=[^\[]\]\().+?(?=\))", self.page)
        for l in proper_links:
            # Get the filename
            link = urllib.parse.unquote(l)

            res = GetObsidianFilePath(link, self.file_tree, self.pb)
            rel_path_str = res['rtr_path_str']
            lo = res['fo']
            if lo == False:
                continue

            # Determine if file is markdown
            if Path(rel_path_str).suffix == '.md':
                isMd = True
    
            if isMd:
                # Add to list to recurse to the link later
                self.links.append(lo)

            # Get file info
            file_link = lo.get_link('markdown', origin=origin)

            # Update link
            new_link = ']('+file_link+')'
            safe_link = re.escape(']('+l+')')
            self.page = re.sub(f"(?<![\[\(])({safe_link})", new_link, self.page)

            if isMd == False:
                # Copy file over to new location
                lo.copy_file('ntm')

        # -- [6] Replace Obsidian links with proper markdown
        # This is any string in between [[ and ]], e.g. [[My Note]]
        md_links = re.findall("(?<=\[\[).+?(?=\])", self.page)
        for l in md_links:
            # A link in Obsidian can have the format 'filename|alias'
            # If a link does not have an alias, the link name will function as the alias.
            parts = l.split('|')
            filename = parts[0].split('/')[-1]

            # Set alias i.e. [alias](link)
            alias = filename
            if len(parts) > 1:
                alias = parts[1]

            # Split #Chapter
            hashpart = ''
            parts = filename.split('#')
            if len(parts) > 1:
                filename = parts[0]
                hashpart = parts[1]

            # Case: hashpart exists, filename is empty --> anchor link
            is_anchor = False
            if hashpart != '' and filename == '':
                is_anchor = True

            if is_anchor == False:
                # find link in filetree
                res = GetObsidianFilePath(l, self.file_tree, self.pb)
                rel_path_str = res['rtr_path_str']
                fo = res['fo']

                if rel_path_str == False:
                    link = '/not_created.md'
                else:
                    link = fo.get_link('markdown', origin=origin)
                    self.links.append(fo)

                newlink = urllib.parse.quote(link)

                if hashpart != '':
                    hashpart = hashpart.replace(' ', '-').lower()
                    newlink += f'#{hashpart}'
            else:
                newlink = '#' + ConvertTitleToMarkdownId(hashpart)
                alias = hashpart

            # Replace Obsidian link with proper markdown link
            self.page = self.page.replace('[['+l+']]', f"[{alias}]({newlink})")


        # -- [7] Fix newline issue by adding three spaces before any newline
        self.page = self.page.replace("\n", "   \n")

        # -- [8] Insert markdown links for bare http(s) links (those without the [name](link) format).
        # Cannot start with [, (, nor "
        # match 'http://* ' or 'https://* ' (end match by whitespace)
        for l in re.findall("(?<![\[\(\"])(https*:\/\/.[^\s]*)", self.page):
            new_md_link = f"[{l}]({l})"
            safe_link = re.escape(l)
            self.page = re.sub(f"(?<![\[\(])({safe_link})", new_md_link, self.page)

        # -- [9] Remove inline tags, like #ThisIsATag
        # Inline tags are # connected to text (so no whitespace nor another #)
        for l in re.findall("(?<!\S)#[^\s#`]+", self.page):
            tag = l.replace('.', '').replace('#', '')
            new_md_str = f"**{tag}**"

            self.add_tag(tag)

            safe_str = re.escape(l)
            self.page = re.sub(safe_str, new_md_str, self.page)
            
        # -- [10] Add code inclusions
        for l in re.findall(r'^(\<inclusion href="[^"]*" />)', self.page, re.MULTILINE):
            link = l.replace('<inclusion href="', '').replace('" />', '')
            
            result = GetObsidianFilePath(link, self.file_tree, self.pb)
            file_object = result['fo']
            header =  result['header']

            if file_object == False:
                self.page = self.page.replace(l, f"> **obsidian-html error:** Could not find page {link}.")
                continue
            
            self.links.append(file_object)

            if include_depth > 3:
                link_path = file_object.get_link('markdown', origin=origin)
                self.page = self.page.replace(l, f"[{link}]({link_path}).")
                continue

            incl_page_path = file_object.path['note']['file_absolute_path']
            if not file_object.is_valid_note('note'):
                self.page = self.page.replace(l, f"> **obsidian-html error:** Error including file or not a markdown file {link}.")
                continue
            
            # Get code
            included_page = MarkdownPage(self.pb, file_object, 'note', self.file_tree)
            included_page.ConvertObsidianPageToMarkdownPage(origin=self.fo, include_depth=include_depth + 1, includer_page_depth=page_folder_depth)

            # Get subsection of code if header is present
            if header != '':
                header_id = ConvertTitleToMarkdownId(header)
                included_page.StripCodeSections()
                header_dict, root_element = ConvertMarkdownToHeaderTree(included_page.page)
                included_page.page = PrintHeaderTree(header_dict[header_id])
                included_page.RestoreCodeSections()
            
            self.page = self.page.replace(l, included_page.page + '\n')

        # -- [1] Restore codeblocks/-lines
        self.RestoreCodeSections()

        return self
