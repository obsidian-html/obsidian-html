"""
Eraser Extension for Python-Markdown
========================================

Obisidian has a comment system: everything between %% is a comment and will not be shown in view mode

    Text
    %%
    comment block
    %%
    Text

    Text %% inline comment %% text

This extension removes these comments. 
%% in codelines/-blocks are ignored.

"""

from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor


# ------------------ The Markdown Extension -------------------------------


class EraserExtension(Extension):
    """Remove blocks enclosed by certain characters, such as %%%."""

    # def __init__(self, **kwargs):
    #     self.config = {
    #         'opening_sequence' : ['not_set', 'Regex value to start erasing. Entire line will be removed'],
    #         'closing_sequence' : ['not_set', 'Regex value to stop erasing. Current line will still be removed'],
    #         'homogenous' :       [False, 'Whether the opening sequence will also function as closing sequence'],
    #         'verbose' :          [False, 'Whether to print output']
    #     }
    #     super(EraserExtension, self).__init__(**kwargs)

    def extendMarkdown(self, md):
        """Add EraserExtension to Markdown instance."""
        # Insert a preprocessor before ReferencePreprocessor
        md.preprocessors.register(EraserPreprocessor(self, md), "eraser", 35)
        md.registerExtension(self)


def makeExtension(**kwargs):  # pragma: no cover
    return EraserExtension(**kwargs)


class EraserPreprocessor(Preprocessor):
    def __init__(self, extension, md=None):
        self.md = md
        # self.extension = extension
        # self.verbose = self.extension.getConfig('verbose')

    # def verbose_print(self, msg):
    #     if self.verbose:
    #         print(f"eraser extension: {msg}")

    def run(self, lines):
        in_comment = 0
        in_codeblock = 0
        in_codeline = 0

        new_lines = []
        for line in lines:
            new_line = ""
            for i, char in enumerate(line):
                if char == "`":
                    # we can be in a ``` block, `` block, or a singular `
                    # singular is easy to test, no ` neighbours will be present
                    if next_char(line, i) != "`" and prev_char(line, i) != "`":
                        # -[`]- singular backtick
                        if in_codeline:
                            in_codeline = 0
                            # new_line += '<intext>'
                        else:
                            in_codeline = 1
                            # new_line += '<incodeline>'

                    # We only act when we are at the end of a ``` block the character before the ``` should not be a `
                    if prev_char(line, i) == "`" and val(line, i - 2) == "`" and val(line, i - 3) != "`":
                        # ``[`] codeblock
                        if in_codeblock:
                            in_codeblock = 0
                            # new_line += '<intext>'
                        else:
                            in_codeblock = 1
                            # new_line += '<incodeblock>'

                    # `` will have no effect on us, so no need to test for it

                if (not in_codeblock) and (not in_codeline):
                    if char == "%":
                        if next_char(line, i) == "%":
                            continue
                        if prev_char(line, i) == "%":
                            if in_comment:
                                in_comment = 0
                                # new_line += '<intext>'
                            else:
                                in_comment = 1
                                # new_line += '<incomment>'
                            continue

                if not in_comment:
                    new_line += char

            if line.strip() != "" and new_line.strip() == "":
                pass
            else:
                new_lines.append(new_line)

        return new_lines


def val(arr, index):
    if index < 0:
        return False
    if index > (len(arr) - 1):
        return False
    return arr[index]


def next_char(arr, index):
    return val(arr, index + 1)


def prev_char(arr, index):
    return val(arr, index - 1)
