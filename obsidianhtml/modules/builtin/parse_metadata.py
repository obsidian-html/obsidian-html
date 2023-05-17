import os
import yaml
import frontmatter
import regex as re

from pathlib import Path

from ...core.FileObject import FileObject
from ...parser.MarkdownPage import MarkdownPage

from ..base_classes import ObsidianHtmlModule


class ParseMetadataModule(ObsidianHtmlModule):
    """
    This module will load all the files in index/markdown_files.json and load the metadata and inline tags, which are combined
    and the result is written to index/metadata.json
    """

    @property
    def requires(self):
        return tuple(["paths.json", "index/markdown_files.json"])

    @property
    def provides(self):
        return tuple(["index/metadata.json"])

    @property
    def alters(self):
        return tuple()

    def accept(self, module_data_folder):
        """This function is run before run(), if it returns False, then the module run is skipped entirely. Any other value will be accepted"""
        return

    def sanatize_frontmatter(self, metadata):
        # imitate obsidian shenannigans
        if "tags" in metadata.keys():
            tags = metadata["tags"]
            if isinstance(tags, str):
                if " " in tags.strip() or "," in tags:
                    metadata["tags"] = [x.rstrip(",") for x in tags.replace(",", " ").split(" ") if x != ""]
                elif tags.strip() == "":
                    metadata["tags"] = []
                else:
                    metadata["tags"] = [tags,]
            elif tags is None:
                metadata["tags"] = []
        else:
            metadata["tags"] = []
        return metadata

    def get_frontmatter(self, file_path):
        with open(file_path, encoding="utf-8") as f:
            metadata, page = frontmatter.parse(f.read())
        return self.sanatize_frontmatter(metadata), page

    def get_inline_tags(self, page):
        return [x[1:].replace(".", "") for x in re.findall(r"(?<!\S)#[\w/\-]*[a-zA-Z\-_/][\w/\-]*", page)]

    def run(self):
        # get input
        files = self.modfile("index/markdown_files.json").read().from_json()
        paths = self.modfile("paths.json").read().from_json()

        # handle files
        output = {}
        for file in files:
            rel_path = Path(file).relative_to(paths["input_folder"]).as_posix()
            metadata = {}
            metadata["tags"] = []
            try:
                metadata, page = self.get_frontmatter(file)
                inline_tags = self.get_inline_tags(page)
                metadata["tags"] = list(set(metadata["tags"] + inline_tags))
            except Exception as e:
                self.print('ERROR', f'failed to parse metadata in file: {file}. Error: {e}. \n\n(Ignoring this error is not supported as metadata will be read elsewhere. Review yaml frontmatter and edit it to resolve the issue).')
                exit(1)
            output[rel_path] = metadata

        self.modfile("index/metadata.json", output).to_json().write()


    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def integrate_save(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass