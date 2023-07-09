from __future__ import annotations
import string
import regex as re  # regex string finding/replacing
from pathlib import Path
import frontmatter  # remove yaml frontmatter from md files
import urllib.parse  # convert link characters like %

from ..lib import slugify, MalformedTags, OpenIncludedFile, bisect, strip_frontmatter
from .. import note2md
from ..core import FileObject

from .HeaderTree import PrintHeaderTree, convert_markdown_to_header_tree, get_referenced_block, GetSubHeaderTree


class MarkdownPage:
    page = None  # Pure markdown code read from src file
    yaml = None  # Yaml is stripped from the src file and saved here
    codeblocks = None  # used to safely store ```codeblock content
    codelines = None  # Used to safely store `codeline` content
    links = None  # Used to recurse to any page linked to by this page

    src_path = None  # Path() object of src file
    rel_src_path = None  # Path() object relative to given markdown root folder (src_folder_path)
    dst_folder_path = None  # Path() object of given markdown output folder
    dst_path = None  # Path() object of destination file

    isEntryPoint = False

    file_tree = None  # Tree of files that are found in the root folder

    def __init__(self, fo: "FileObject", input_type):
        self.pb = fo.pb
        self.fo = fo
        self.file_tree = self.pb.index.files

        self.src_path = fo.path[input_type]["file_absolute_path"]
        self.rel_src_path = fo.path[input_type]["file_relative_path"]
        self.input_type = input_type

        self.links = []
        self.codeblocks = []
        self.codelines = []

        # Load contents of entrypoint and strip frontmatter yaml.
        with open(self.src_path, encoding="utf-8") as f:
            self.page = strip_frontmatter(f.read())

        key = fo.path[input_type]["og_file_relative_path"].as_posix()
        if key not in self.pb.metadata:
            self.metadata = {}
            self.metadata["tags"] = []
        else:
            self.metadata = self.pb.metadata[key]


    def HasTag(self, ttag):
        tags = self.metadata["tags"]
        for tag in tags:
            if ttag == tag:
                return True
            parts = tag.split("/")
            root = parts[0]
            if ttag == root:
                return True
            if len(parts) > 1:
                for part in parts[1:]:
                    root = root + "/" + part
                    if ttag == root:
                        return True
        return False

    # [425] Add included references as links in graph view
    def AddInclusionLink(self, relative_md_path):
        if "obs.html.data" not in self.metadata:
            self.metadata["obs.html.data"] = {}
        if "inclusion_references" not in self.metadata["obs.html.data"]:
            self.metadata["obs.html.data"]["inclusion_references"] = []
        if relative_md_path not in self.metadata["obs.html.data"]["inclusion_references"]:
            self.metadata["obs.html.data"]["inclusion_references"].append(relative_md_path)

    def GetNodeName(self):
        if "graph_name" in self.metadata.keys():
            return self.metadata["graph_name"]
        else:
            return self.fo.path["markdown"]["file_relative_path"].stem

    def StripCodeSections(self):
        """(Temporarily) Remove codeblocks/-lines so that they are not altered in all the conversions. Placeholders are inserted."""
        self.codeblocks = re.findall(r"^```([\s\S]*?)```[\s]*?$", self.page, re.MULTILINE)
        for i, match in enumerate(self.codeblocks):
            self.page = self.page.replace("```" + match + "```", f"%%%codeblock-placeholder-{i}%%%")

        self.codelines = re.findall("`(.*?)`", self.page)
        for i, match in enumerate(self.codelines):
            self.page = self.page.replace("`" + match + "`", f"%%%codeline-placeholder-{i}%%%")

        self.latexblocks = re.findall(r"^\$\$([\s\S]*?)\$\$[\s]*?$", self.page, re.MULTILINE)
        for i, match in enumerate(self.latexblocks):
            self.page = self.page.replace("$$" + match + "$$", f"%%%latexblock-placeholder-{i}%%%")

    def RestoreCodeSections(self):
        """Undo the action of StripCodeSections."""
        for i, value in enumerate(self.latexblocks):
            self.page = self.page.replace(f"%%%latexblock-placeholder-{i}%%%", f"$${value}$$")
        for i, value in enumerate(self.codelines):
            self.page = self.page.replace(f"%%%codeline-placeholder-{i}%%%", f"`{value}`")
        for i, value in enumerate(self.codeblocks):
            self.page = self.page.replace(f"%%%codeblock-placeholder-{i}%%%", f"```{value}```\n")

    def strip_svgs(self):
        self.svgs = []
        i = 0
        for matched_block in re.findall(r"<svg[\s\S]*?</svg>", self.page):
            new_link = "---obsidian_html_svg_block_" + str(i)
            self.svgs.append(matched_block)
            i += 1

            safe_link = re.escape(matched_block)
            self.page = re.sub(safe_link, new_link, self.page)

        return self.svgs

    def restore_svgs(self):
        for i, v in enumerate(self.svgs):
            self.page = self.page.replace("---obsidian_html_svg_block_" + str(i), v)

    def add_tag(self, tag):
        if "tags" not in self.metadata:
            self.metadata["tags"] = []
        if tag not in self.metadata["tags"]:
            self.metadata["tags"].append(tag)

    def get_tags(self):
        if "tags" not in self.metadata:
            return []
        return self.metadata["tags"]

    def AddToTagtree(self, tagtree, url=""):
        if url == "":
            url = self.fo.get_link("html")

        # collect tags
        tags = self.get_tags()

        for tag in self.get_tags():
            # test is str
            if not isinstance(tag, str):
                raise MalformedTags(f"Tag {tag} in frontmatter of \"{self.src_path}\" is of type {type(tag)}, but should be a string. (Items under 'tags:' can not include a ':' on its line).")

            # add tag in correct place in the tagtree
            ctagtree = tagtree
            for n, subtag in enumerate(tag.split("/")):
                if subtag not in ctagtree["subtags"].keys():
                    ctagtree["subtags"][subtag] = {"notes": [], "subtags": {}}
                ctagtree = ctagtree["subtags"][subtag]

                if n == (len(tag.split("/")) - 1):
                    ctagtree["notes"].append((self.fo, url))

    def GetVideoHTML(self, file_name, relative_path_corrected, suffix):
        mime_type_lut = {
            "mp4": "video/mp4",
            "webm": "video/webm",
            "flv": "video/x-flv",
            "3gp": "video/3gpp",
            "mov": "video/quicktime",
            "wmv": "video/x-ms-wmv",
            "avi": "video/x-msvideo",
            "ogv": "video/ogg",
            "mkv": "video/x-matroska",
        }
        if suffix not in mime_type_lut:
            mime_type = ""
        else:
            mime_type = mime_type_lut[suffix]

        video_template = OpenIncludedFile("html/templates/video_template.html")
        return video_template.replace("{url}", relative_path_corrected).replace("{mime_type}", mime_type)

    def GetAudioHTML(self, file_name, relative_path_corrected, suffix):
        mime_type_lut = {
            "mp3": "audio/mpeg",
            "webm": "audio/webm",
            "m4a": "audio/mp4",
            "wav": "audio/x-wav",
            "ogg": "audio/ogg",
            "3gp": "video/3gpp",
            "flac": "audio/flac",
        }
        if suffix not in mime_type_lut:
            mime_type = ""
        else:
            mime_type = mime_type_lut[suffix]

        audio_template = OpenIncludedFile("html/templates/audio_template.html")
        return audio_template.replace("{url}", relative_path_corrected).replace("{mime_type}", mime_type)

    def GetEmbeddable(self, file_name, relative_path_corrected, suffix):
        return f'<embed src="{relative_path_corrected}" width="90%" height="700px">'

    def GetImageHTML(self, relative_path_corrected, width, alt):
        image_template = OpenIncludedFile("html/templates/image_template.html")
        return image_template.replace("{relative_path}", urllib.parse.quote(relative_path_corrected)).replace("{width}", width).replace("{alt}", alt)

    def ConvertObsidianPageToMarkdownPage(self, origin: "FileObject" = None, include_depth=0, includer_page_depth=None, remove_block_references=True):
        """Full subroutine converting the Obsidian Code to proper markdown. Linked files are copied over to the destination folder."""

        # -- Set origin (calling page), this will always be self.fo unless origin is passed in
        if origin is None:
            origin = self.fo

        # -- Get page depth
        page_folder_depth = self.fo.metadata["depth"]

        if includer_page_depth is not None:
            page_folder_depth = includer_page_depth
            # overwrite
            if self.fo.metadata["is_entrypoint"]:
                page_folder_depth = 0

        # -- [??] Remove spaces in front of codeblock open and close lines
        # Obisidian allows spaces in front, markdown does not
        self.page = re.sub(r"(^ *```)", "```", self.page, flags=re.MULTILINE)

        # -- [1] Replace code blocks with placeholders so they aren't altered
        # They will be restored at the end
        self.StripCodeSections()

        # -- [??] Insert extra newline between two centered mathjax blocks
        self.page = re.sub(r"\$\$\ *\n\$\$", "$$ \n\n$$", self.page, flags=re.MULTILINE)

        # -- [??] Replace \| with |
        self.page = re.sub(r"\\\|", "|", self.page, flags=re.MULTILINE)

        # -- [2] Add newline between paragraph and lists
        def is_list_line(line):
            line = line.strip()
            # dash list items
            if line.startswith("- "):
                return True
            # asterisk list items
            if line.startswith("* "):
                return True
            return False

        buffer = ""
        prev_is_list_line = False
        prev_is_newline = False
        for i, line in enumerate(self.page.split("\n")):
            current_is_list_line = is_list_line(line)
            current_is_newline = len(line.strip()) == 0
            if current_is_list_line and (prev_is_list_line is False) and (prev_is_newline is False):
                # newline before list
                buffer += "\n"
            if (current_is_list_line is False) and (current_is_newline is False) and prev_is_list_line:
                # newline after list
                buffer += "\n"
            # add current line
            buffer += "\n" + line
            # move data
            prev_is_list_line = current_is_list_line
            prev_is_newline = current_is_newline
        self.page = buffer

        # -- [?] Remove whitespace in front of header hashtags
        self.page = re.sub("(^\ [\ ]*)(?=#)", "", self.page, flags=re.MULTILINE)

        # [??] Embedded note titles integration
        # ------------------------------------------------------------------
        self.page = note2md.add_embedded_title(self.pb, self.page, self.metadata, self.GetNodeName())

        # -- [3] Convert Obsidian type img links to proper md image links
        # Further conversion will be done in the block below
        self.page = note2md.obs_img_to_md_img(self.pb, self.page)

        for tag in re.findall(r'<img src=".*?/>', self.page):
            # get template and link from tag
            # e.g. <img src="200w.gif"  width="200"> --> <img src="{link}"  width="200"> & 200w.gif
            parts = tag.split('src="')
            iparts = parts[1].split('"', 1)
            link = iparts[0]

            template = parts[0] + 'src="{link}"'
            if len(iparts) > 1:
                template = template + iparts[1]

            unquoted_link = urllib.parse.unquote(link)
            if "://" in unquoted_link:
                continue

            # Find file
            rel_path_str, lo = self.pb.FileFinder.FindFile(link, self.pb)
            if rel_path_str is False:
                if self.pb.gc("toggles/verbose_printout", cached=True):
                    print(f"\t\tImage/file with obsidian link of '{link}' will not be copied over in this step.")
                    if "://" in link:
                        print("\t\t\t<continued> The link seems to be external (contains ://)")
                    else:
                        print(f"\t\t\t<continued> The link was not found in the file tree. Clean links in the file tree are: {', '.join(self.file_tree.keys())}")
                continue

            # Get shorthand info
            relative_path = lo.path["markdown"]["file_relative_path"]

            # Copy file over to markdown destination
            lo.copy_file("ntm")

            # Adjust link in page
            file_name = urllib.parse.unquote(link)
            relative_path = relative_path.as_posix()
            relative_path = ("../" * page_folder_depth) + relative_path
            new_link = template.replace("{link}", urllib.parse.quote(relative_path))

            safe_link = re.escape(tag)
            self.page = re.sub(safe_link, new_link, self.page)

        # -- [4] Handle local image/video/audio links (copy them over to output)
        for tag, link in re.findall("(?<=\!\[(.*?)\]\()(.*?)(?=\))", self.page):
            unq_link = urllib.parse.unquote(link)

            # clean_link_name = urllib.parse.unquote(link).split('/')[-1].split('|')[0]
            clean_link = unq_link.split("|")[0]
            if clean_link.strip() == "":
                continue

            # Find file
            rel_path_str, lo = self.pb.FileFinder.FindFile(clean_link, self.pb)
            if rel_path_str is False:
                if self.pb.gc("toggles/verbose_printout", cached=True):
                    print(f"\t\tImage/file with obsidian link of '{clean_link}' (original {link}) will not be copied over in this step.")
                    if "://" in link:
                        print("\t\t\t<continued> The link seems to be external (contains ://)")
                    else:
                        print(f"\t\t\t<continued> The link was not found in the file tree. Clean links in the file tree are: {', '.join(self.file_tree.keys())}")
                continue

            # Get shorthand info
            suffix = lo.path["note"]["suffix"]
            relative_path = lo.path["markdown"]["file_relative_path"]

            # Copy file over to markdown destination
            lo.copy_file("ntm")

            # Adjust link in page
            file_name = urllib.parse.unquote(link)
            relative_path = relative_path.as_posix()
            relative_path = ("../" * page_folder_depth) + relative_path
            new_link = f"![{tag}](" + urllib.parse.quote(relative_path) + ")"

            # Handle video/audio usecase
            if lo.metadata["is_video"]:
                new_link = self.GetVideoHTML(file_name, relative_path, suffix)
            elif lo.metadata["is_audio"]:
                new_link = self.GetAudioHTML(file_name, relative_path, suffix)
            elif lo.metadata["is_embeddable"]:
                new_link = self.GetEmbeddable(file_name, relative_path, suffix)
            elif tag != "":
                width = ""
                alt = ""
                if tag.isdigit():
                    width = tag
                elif "|" in tag:
                    parts = tag.split("|")
                    if parts[-1].isdigit():
                        width = parts.pop()
                    alt = "".join(parts)
                else:
                    alt = tag
                if alt.strip() and self.pb.gc("toggles/img_alt_text_use_figure", cached=True):
                    new_link = self.GetImageHTML(relative_path, width, alt)
                else:
                    new_link = f'<img src="{urllib.parse.quote(relative_path)}" width="{width}" alt="{alt}" title="{alt}" />'

            safe_link = re.escape(f"![{tag}](" + link + ")")
            self.page = re.sub(safe_link, new_link, self.page)

        # -- [5] Change file name in proper markdown links to path
        # And while we are busy, change the path to point to the full relative path
        proper_links = re.findall(r"(?<=\]\()[^\s\]]+(?=\))", self.page)
        for matched_link in proper_links:
            # There is currently no way to match links containing parentheses, AND not matching the last ) in a link like ([test](link))
            if matched_link.endswith(")"):
                matched_link = matched_link[:-1]

            # Get the filename
            link = urllib.parse.unquote(matched_link)

            if not link.startswith("#"):
                res = self.pb.FileFinder.GetObsidianFilePath(link, self.pb)
                rel_path_str = res["rtr_path_str"]
                lo = res["fo"]
                if lo is False:
                    continue

                # Determine if file is markdown
                isMd = Path(rel_path_str).suffix == ".md"
                if isMd:
                    # Add to list to recurse to the link later
                    self.links.append(lo)

                # Get file info
                file_link = lo.get_link("markdown", origin=origin)

                # Update link
                new_link = "](" + urllib.parse.quote(file_link) + ")"
                safe_link = re.escape("](" + matched_link + ")")
                self.page = re.sub(f"(?<![\[\(])({safe_link})", new_link, self.page)

                if isMd is False:
                    # Copy file over to new location
                    lo.copy_file("ntm")

        # -- [6] Replace Obsidian links with proper markdown
        # This is any string in between [[ and ]], e.g. [[My Note]]
        md_links = re.findall("(?<=\[\[).+?(?=\])", self.page)
        for matched_link in md_links:
            rest, alias = bisect(matched_link, "|")
            simple_path, hashpart = bisect(rest, "#", squash_tail=True)  # hashpart can have more than 1 #!
            filename = simple_path.split("/")[-1]

            if alias == "":
                alias = filename

            # Case: hashpart exists, filename is empty --> anchor link
            is_anchor = False
            if hashpart != "" and filename == "":
                is_anchor = True

            if is_anchor is False:
                # find link in filetree
                res = self.pb.FileFinder.GetObsidianFilePath(matched_link, self.pb)
                rel_path_str = res["rtr_path_str"]
                fo = res["fo"]

                if rel_path_str is False:
                    link = "/not_created.md"
                else:
                    link = fo.get_link("markdown", origin=origin)
                    if not fo.metadata["is_note"]:
                        fo.copy_file("ntm")
                    else:
                        self.links.append(fo)
                newlink = urllib.parse.quote(link)

                if hashpart != "":
                    hashpart = hashpart.replace(" ", "-").lower()
                    hashpart = make_valid_hashpart(hashpart)
                    newlink += "#" + hashpart
            else:
                if hashpart[0] == "^":
                    # blockid blocklink
                    newlink = "#" + hashpart.replace("^", "__")
                else:
                    # normal anchor
                    newlink = "#" + make_valid_hashpart(slugify(hashpart))
                    alias = hashpart

            # Replace Obsidian link with proper markdown link
            self.page = self.page.replace("[[" + matched_link + "]]", f"[{alias}]({newlink})")

        # -- [7] Fix newline issue by adding three spaces before any newline
        if not self.pb.gc("toggles/strict_line_breaks"):
            self.page = self.page.replace("\n", "   \n")

        # -- [8] Insert markdown links for bare http(s) links (those without the [name](link) format).
        # Cannot start with [, (, nor "
        # match 'http://* ' or 'https://* ' (end match by whitespace)
        matched_links = re.findall(r"(?<![\[\(\"])(https*:\/\/.[^\s|]*)", self.page)

        # sort from longest to shortest to avoid links with the same base being partly overwritten
        matched_links.sort(reverse=True, key=lambda e: len(e))

        for matched_link in matched_links:
            new_md_link = f"[{matched_link}]({matched_link})"
            safe_link = re.escape(matched_link)
            self.page = re.sub(f"(?<![\[\(])({safe_link})", new_md_link, self.page)

        # --- strip svg, we don't want to find "tags" in there
        self.strip_svgs()

        # -- [9] Remove inline tags, like #ThisIsATag
        # Inline tags are # connected to text (so no whitespace nor another #)
        for matched_link in get_inline_tags(self.page):
            tag = matched_link.replace(".", "")
            new_md_str = f"**{tag}**"

            if self.pb.gc("toggles/preserve_inline_tags", cached=True):
                new_md_str = "`{_obsidian_pattern_tag_" + tag + "}`"

            self.add_tag(tag)

            safe_str = "#" + re.escape(matched_link) + r"(?=[^\p{L}\p{N}/\-\p{Emoji_Presentation}]|$)"  # avoid head replacement error
            self.page = re.sub(safe_str, new_md_str, self.page)

        # --- restore svg, we don't want to find "tags" in there
        self.restore_svgs()

        # -- [10] Add code inclusions
        for matched_link in re.findall(r'(\<inclusion href="[^"]*" />)', self.page, re.MULTILINE):
            link = matched_link.replace('<inclusion href="', "").replace('" />', "")

            result = self.pb.FileFinder.GetObsidianFilePath(link, self.pb)
            file_object = result["fo"]
            header = result["header"]

            if file_object is False:
                self.page = self.page.replace(matched_link, f"> **obsidian-html error:** Could not find page {link}.")
                continue

            self.links.append(file_object)
            link_path = file_object.get_link("markdown", origin=origin)

            if include_depth > 3:
                self.page = self.page.replace(matched_link, f"[{link}]({link_path}).")
                continue

            if not file_object.is_valid_note("note"):
                # make download button
                file_object.copy_file("ntm")
                self.page = self.page.replace(matched_link, f"[{link_path}]({urllib.parse.quote(link)}|_obsidian_html_download_button_)")
                continue

            # Get code
            # included_page = MarkdownPage(self.pb, file_object, 'note', self.file_tree)
            included_page = file_object.load_markdown_page("note")
            included_page.ConvertObsidianPageToMarkdownPage(origin=self.fo, include_depth=include_depth + 1, includer_page_depth=page_folder_depth, remove_block_references=False)

            # Get subsection of code if header is present
            if header != "":
                # Prepare document
                included_page.StripCodeSections()

                # option: Referencing block
                if header[0] == "^":
                    included_page.page = get_referenced_block(header, included_page.page, included_page.rel_src_path.as_posix())

                # option: Referencing header
                else:
                    header_dict, root_element = convert_markdown_to_header_tree(included_page.page)
                    header_tree = GetSubHeaderTree(root_element, header)
                    if header_tree is False:
                        included_page.page = f"Obsidianhtml: Error: Unable to find section #{header} in {link.split('#')[0]}"
                    else:
                        included_page.page = PrintHeaderTree(header_tree)

                # Wrap up
                included_page.RestoreCodeSections()

            self.page = self.page.replace(matched_link, "\n" + included_page.page + "\n")

            # [425] Add included references as links in graph view
            # add link to frontmatter yaml so that we can add it to the graphview
            if self.pb.gc("toggles/features/graph/show_inclusions_in_graph"):
                self.AddInclusionLink(result["rtr_path_str"])
        # -- [1] Restore codeblocks/-lines
        self.RestoreCodeSections()

        return self


def get_inline_tags(page):
    tags = [x[1:].replace(".", "") for x in re.findall(r"(?<!\S)#[\p{L}\p{N}/\-\p{Emoji_Presentation}]*[\p{L}\-_/\p{Emoji_Presentation}][\p{L}\p{N}/\-\p{Emoji_Presentation}]*", page)]
    return tags


def make_valid_hashpart(hashpart):
    """
    This operation aims to solve the "Failed to execute 'querySelector' on 'Element': <> is not a valid selector."
    By adding "h_" to the beginning if the hashpart does not start with a letter.
    Be sure to also have this be applied in: obsidianhtml/markdown_extensions/CustomTocExtension.py ! (search for el.attrib["id"])
    """
    if hashpart == "":
        return hashpart

    if hashpart[0] in string.ascii_letters:
        return hashpart

    return "h_" + hashpart
