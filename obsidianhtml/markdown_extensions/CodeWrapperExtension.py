from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

import re

RegexBegin = re.compile(r"^\ *\`\`\`")
RegexEnd = re.compile(r"^\ *\`\`\`")


class CodeWrapperExtension(Extension):
    # def __init__(self, **kwargs):
    #     self.config = {
    #         'note_path' : ['not set', 'Path to the note relative to the vault'],
    #         'dataview_export_folder' : ['not set', 'Absolute path to the dataview export folder']
    #     }
    #     super(CodeWrapperExtension, self).__init__(**kwargs)

    """Add source code hilighting to markdown codeblocks."""

    def extendMarkdown(self, md):
        md.preprocessors.register(CodeWrapperPreprocessor(self, md), "code_wrapper", 35)
        md.registerExtension(self)


def makeExtension(**kwargs):
    return CodeWrapperExtension(**kwargs)


class CodeWrapperPreprocessor(Preprocessor):
    def __init__(self, extension, md=None):
        self.md = md
        self.extension = extension

    def run(self, lines):
        new_lines = []
        m_start = None
        m_end = None
        in_code = False
        lang = ""

        for line in lines:
            m_start = None
            m_end = None

            if not in_code:
                m_start = RegexBegin.match(line)
                if m_start:
                    lang = line.replace("```", "").strip()
                    if lang == "":
                        lang = "general"
                    new_lines.append(f'<div class="lang-{lang}">')
                    in_code = True
                # else:
                new_lines.append(line)
            else:
                new_lines.append(line)
                m_end = RegexEnd.match(line)
                if m_end:
                    in_code = False
                    new_lines.append("</div>")

        return new_lines
