"""
Implement internal links to specific annotated blocks. See also:
https://github.com/obsidian-html/obsidian-html/issues/533
https://help.obsidian.md/Linking+notes+and+files/Internal+links
"""

from markdown.extensions import Extension
from markdown.blockprocessors import BlockProcessor
import xml.etree.ElementTree as etree


def makeExtension(**kwargs):  # pragma: no cover
    return BlockLinkExtension(**kwargs)


class BlockLinkExtension(Extension):
    def extendMarkdown(self, md):
        md.parser.blockprocessors.register(BlockLinkBlockProcessor(md.parser), "BlockLinkExtension", 175)


class BlockLinkBlockProcessor(BlockProcessor):
    # def __init__(self, parser):
    #     """Initialization."""

    #     super().__init__(parser)

    def test(self, parent, block):
        lines = block.split("\n")
        if len(lines) > 0 and len(lines[-1]) > 0:
            if lines[-1][0] == "^" and " " not in lines[-1][0]:
                return True
        return False

    def run(self, parent, blocks):
        block = blocks.pop(0)

        # split off last line
        lines = block.split("\n")
        marker = lines.pop().strip().replace("^", "__")

        div = etree.SubElement(parent, "div")
        div.set("id", marker)
        self.parser.parseChunk(div, "\n".join(lines))

        return True
