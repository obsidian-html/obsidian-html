from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

import regex as re

RegexBegin = re.compile(r"^ *\`\`\` *ad-cite")
RegexEnd = re.compile(r"^ *\`\`\`")


class AdmonitionExtension(Extension):
    # def __init__(self, **kwargs):
    #     self.config = {
    #         'note_path' : ['not set', 'Path to the note relative to the vault'],
    #         'dataview_export_folder' : ['not set', 'Absolute path to the dataview export folder']
    #     }
    #     super(AdmonitionExtension, self).__init__(**kwargs)

    """Add source code hilighting to markdown codeblocks."""

    def extendMarkdown(self, md):
        md.preprocessors.register(AdmonitionPreprocessor(self, md), "admonition2", 36)
        md.registerExtension(self)


def makeExtension(**kwargs):
    return AdmonitionExtension(**kwargs)


class AdmonitionPreprocessor(Preprocessor):
    def __init__(self, extension, md=None):
        self.md = md
        self.extension = extension

    def run(self, lines):
        new_lines = []
        m_start = None
        m_end = None
        in_code = False

        for line in lines:
            m_start = None
            m_end = None

            if not in_code:
                m_start = RegexBegin.match(line)
                if m_start:
                    new_lines.append('<div class="ad-cite">')
                    in_code = True
                else:
                    new_lines.append(line)
            else:
                # in code
                m_end = RegexEnd.match(line)

                if line.startswith("title:"):
                    title = line.replace("title:", "").strip()
                    title_code = f'<div class="ad-cite-title"><div class="admonition-title-icon"><svg aria-hidden="true" focusable="false" data-prefix="fas" data-icon="quote-right" role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><path fill="currentColor" d="M464 32H336c-26.5 0-48 21.5-48 48v128c0 26.5 21.5 48 48 48h80v64c0 35.3-28.7 64-64 64h-8c-13.3 0-24 10.7-24 24v48c0 13.3 10.7 24 24 24h8c88.4 0 160-71.6 160-160V80c0-26.5-21.5-48-48-48zm-288 0H48C21.5 32 0 53.5 0 80v128c0 26.5 21.5 48 48 48h80v64c0 35.3-28.7 64-64 64h-8c-13.3 0-24 10.7-24 24v48c0 13.3 10.7 24 24 24h8c88.4 0 160-71.6 160-160V80c0-26.5-21.5-48-48-48z"></path></svg></div><div class="ad-cite-title-content">{title}</div></div>'
                    new_lines.append(title_code)
                elif m_end:
                    in_code = False
                    new_lines.append("</div>")
                else:
                    new_lines.append(line)

        return new_lines
