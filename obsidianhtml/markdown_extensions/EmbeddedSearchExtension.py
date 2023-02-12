from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

import re

RegexBegin = re.compile(r"^\ *\`\`\`\ *query")
RegexEnd = re.compile(r"^\ *\`\`\`")


class EmbeddedSearchExtension(Extension):
    # def __init__(self, **kwargs):
    #     self.config = {
    #         'note_path' : ['not set', 'Path to the note relative to the vault'],
    #         'dataview_export_folder' : ['not set', 'Absolute path to the dataview export folder']
    #     }
    #     super(EmbeddedSearchExtension, self).__init__(**kwargs)

    """Add source code hilighting to markdown codeblocks."""

    def extendMarkdown(self, md):
        md.preprocessors.register(EmbeddedSearchPreprocessor(self, md), "embedded_search", 35)
        md.registerExtension(self)


def makeExtension(**kwargs):
    return EmbeddedSearchExtension(**kwargs)


class EmbeddedSearchPreprocessor(Preprocessor):
    def __init__(self, extension, md=None):
        self.md = md
        self.extension = extension

    def run(self, lines):
        qualifier = "standard"
        new_lines = []
        query_lines = []
        m_start = None
        m_end = None
        in_code = False

        for line in lines:
            m_start = None
            m_end = None

            if not in_code:
                m_start = RegexBegin.match(line)
                if m_start:
                    if "list" in line:
                        qualifier = "list"
                    in_code = True
                else:
                    new_lines.append(line)
            else:
                m_end = RegexEnd.match(line)
                if m_end:
                    in_code = False
                    new_lines.append("{_obsidian_html_query:" + qualifier + "|-| " + " ".join(query_lines) + " }")
                    qualifier = "standard"
                    query_lines = []
                else:
                    query_lines.append(line)
                    pass

        return new_lines
