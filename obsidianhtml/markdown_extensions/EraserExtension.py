"""
Eraser Extension for Python-Markdown
========================================

Removes all code between the opening sequence and the closing sequence.
Lines that contain either sequence are removed as well.

Tip: provide raw strings for the sequences.

"""

from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

import regex as re
import string



# ------------------ The Markdown Extension -------------------------------

class EraserExtension(Extension):
    """ Remove blocks enclosed by certain characters, such as %%%. """
    def __init__(self, **kwargs):
        self.config = {
            'opening_sequence' : ['not_set', 'Regex value to start erasing. Entire line will be removed'],
            'closing_sequence' : ['not_set', 'Regex value to stop erasing. Current line will still be removed'], 
            'verbose' :          [False, 'Whether to print output']
        }
        super(EraserExtension, self).__init__(**kwargs)

    def extendMarkdown(self, md):
        """ Add EraserExtension to Markdown instance. """
        # Insert a preprocessor before ReferencePreprocessor
        md.preprocessors.register(EraserPreprocessor(self, md), 'eraser', 35)
        md.registerExtension(self)

def makeExtension(**kwargs):  # pragma: no cover
    return EraserExtension(**kwargs)

class EraserPreprocessor(Preprocessor):
    def __init__(self, extension, md=None):
        self.md = md
        self.extension = extension
        self.verbose = self.extension.getConfig('verbose')

    def verbose_print(self, msg):
        if self.verbose:
            print(f"eraser extension: {msg}")

    def run(self, lines):
        opening_regex = self.extension.getConfig('opening_sequence')
        closing_regex = self.extension.getConfig('closing_sequence')

        if opening_regex == 'not_set':
            raise Exception('Extension config setting opening_regex was not set')
        if closing_regex == 'not_set':
            raise Exception('Extension config setting closing_regex was not set')

        mode = 'read'

        new_lines = []
        for line in lines: 
            if mode == 'read':
                match_start = re.match(opening_regex, line)
                if match_start:
                    mode = 'erase'

            if mode == 'read':
                new_lines.append(line)

            if mode == 'erase':
                self.verbose_print(f'erase: "{line}"')
                match_end = re.match(closing_regex, line)
                if match_end:
                    mode = 'read'
                    self.verbose_print(f'mode: {mode}')

        return new_lines

