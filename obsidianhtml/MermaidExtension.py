"""
Mermaid Extension for Python-Markdown
========================================

Adds mermaid parser (like github-markdown) to standard Python-Markdown code blocks.

Original code Copyright 2018-2020 [Olivier Ruelle].

License: GNU GPLv3

"""

from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

import re
import string

def strip_notprintable(myStr):
    return ''.join(filter(lambda x: x in string.printable, myStr))

MermaidRegex = re.compile(r"^(?P<mermaid_sign>[\~\`]){3}[\ \t]*[Mm]ermaid[\ \t]*$")


# ------------------ The Markdown Extension -------------------------------

class MermaidExtension(Extension):
    """ Add source code hilighting to markdown codeblocks. """

    def extendMarkdown(self, md):
        """ Add HilitePostprocessor to Markdown instance. """
        # Insert a preprocessor before ReferencePreprocessor
        md.preprocessors.register(MermaidPreprocessor(md), 'MermaidExtension', 35)

        md.registerExtension(self)

def makeExtension(**kwargs):  # pragma: no cover
    return MermaidExtension(**kwargs)

class MermaidPreprocessor(Preprocessor):
    def run(self, lines):
        new_lines = []
        mermaid_sign = ""
        m_start = None
        m_end = None
        in_mermaid_code = False
        is_mermaid = False
        for line in lines:
            # Wait for starting line with MermaidRegex (~~~ or ``` following by [mM]ermaid )
            if not in_mermaid_code:
                m_start = MermaidRegex.match(line)
            else:
                m_end = re.match(r"^["+mermaid_sign+"]{3}[\ \t]*$", line)
                if m_end:
                    in_mermaid_code = False

            if m_start:
                in_mermaid_code = True
                mermaid_sign = m_start.group("mermaid_sign")
                if not re.match(r"^[\ \t]*$", old_line):
                    new_lines.append("")
                if not is_mermaid:
                    is_mermaid = True
                    #new_lines.append('<style type="text/css"> @import url("https://cdn.rawgit.com/knsv/mermaid/0.5.8/dist/mermaid.css"); </style>')
                new_lines.append('<div class="mermaid">')
                m_start = None
            elif m_end:
                new_lines.append('</div>')
                new_lines.append("")
                m_end = None
            elif in_mermaid_code:
                new_lines.append(strip_notprintable(line).strip())
            else:
                new_lines.append(line)

            old_line = line

        if is_mermaid:
            new_lines.append('')
            # This will initialize mermaid renderer. It's done only when the HTML document is ready,
            # to ensure the loading of mermaid.js file is finished.
            new_lines.append('''<script>
                    function initializeMermaid() {
                        mermaid.initialize({startOnLoad:true})
                    }
            
                    if (document.readyState === "complete" || document.readyState === "interactive") {
                        setTimeout(initializeMermaid, 1);
                    } else {
                        document.addEventListener("DOMContentLoaded", initializeMermaid);
                    }
            </script>''')

        return new_lines

