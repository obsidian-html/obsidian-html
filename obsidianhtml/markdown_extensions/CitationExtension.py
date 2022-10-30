from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

import re
import string
from pathlib import Path

RegexBegin = re.compile(r"^\ *\`\`\`\ *ad\-cite")
RegexEnd = re.compile(r"^\ *\`\`\`")

class CitationExtension(Extension):
    # def __init__(self, **kwargs):
    #     self.config = {
    #         'note_path' : ['not set', 'Path to the note relative to the vault'],
    #         'dataview_export_folder' : ['not set', 'Absolute path to the dataview export folder']
    #     }
    #     super(CitationExtension, self).__init__(**kwargs)

    """ Add source code hilighting to markdown codeblocks. """
    def extendMarkdown(self, md):
        md.preprocessors.register(CitationPreprocessor(self, md), 'citation', 35)
        md.registerExtension(self)

def makeExtension(**kwargs): 
    return CitationExtension(**kwargs)

class CitationPreprocessor(Preprocessor):
    def __init__(self, extension, md=None):
        self.md = md
        self.extension = extension

    def run(self, lines):
        qualifier = 'standard'
        new_lines = []
        citation_lines = []
        m_start = None
        m_end = None
        in_code = False

        for line in lines:
            m_start = None
            m_end = None

            if not in_code:
                m_start = RegexBegin.match(line)
                if m_start:
                    in_code = True
                else:
                    new_lines.append(line)
            else:
                m_end = RegexEnd.match(line)
                if m_end:
                    in_code = False
                    new_lines.append(f"<div style=\"padding:1rem;background-color: var(--bg-accent);\">{' '.join(citation_lines)}</div>")
                    citation_lines = []
                else:
                    citation_lines.append(line)
                    pass

        return new_lines