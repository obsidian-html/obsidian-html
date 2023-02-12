"""
Formattings Extension for Python-Markdown
=======================================

Based on https://github.com/Python-Markdown/markdown/blob/master/markdown/extensions/footnotes.py
Added inline footnote functionality

"""
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor
import xml.etree.ElementTree as etree


class FormattingExtension(Extension):
    """Formatting Extension."""

    def __init__(self, **kwargs):
        """Setup configs."""

        self.config = {}
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        """Add pieces to Markdown."""
        md.registerExtension(self)
        self.parser = md.parser
        self.md = md

        # ~~strikethrough~~
        FOOTNOTE_RE = r"~~(.*?)~~"
        md.inlinePatterns.register(FormattingInlineProcessor(FOOTNOTE_RE, self, mode="strikethrough"), "formatting_strikethrough", 175)

        # ==highlight==
        FOOTNOTE_RE_INLINE = r"==(.*?)=="
        md.inlinePatterns.register(FormattingInlineProcessor(FOOTNOTE_RE_INLINE, self, mode="highlight"), "formatting_highlight", 174)


class FormattingInlineProcessor(InlineProcessor):
    """InlinePattern for footnote markers in a document's body text."""

    def __init__(self, pattern, extension, mode=False):
        super().__init__(pattern)
        self.extension = extension

        if mode is False:
            raise Exception("Mode should not be false")

        self.mode = mode

    def handleMatch(self, m, data):
        if self.mode == "strikethrough":
            el = etree.Element("span")
            el.set("class", "formatting_strikethrough")
        else:
            el = etree.Element("mark")
            el.set("class", "formatting_highlight")

        el.text = m.group(1)

        return el, m.start(0), m.end(0)


def makeExtension(**kwargs):  # pragma: no cover
    """Return an instance of the FormattingExtension"""
    return FormattingExtension(**kwargs)
