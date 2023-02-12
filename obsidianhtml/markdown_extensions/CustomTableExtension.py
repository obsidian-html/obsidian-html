from markdown.extensions import Extension
from markdown.blockprocessors import BlockProcessor
import re
import xml.etree.ElementTree as etree


def makeExtension(**kwargs):  # pragma: no cover
    return CustomTableExtension(**kwargs)


class CustomTableExtension(Extension):
    def extendMarkdown(self, md):
        md.parser.blockprocessors.register(CustomTableProcessor(md.parser), "custom_tables", 175)


class CustomTableProcessor(BlockProcessor):
    RE_FENCE_START = r"\|.*\n\|[\s:-]*\|"  # match first two lines of a table

    def __init__(self, parser):
        """Initialization."""
        super().__init__(parser)

    def test(self, parent, block):
        return re.match(self.RE_FENCE_START, block)

    def run(self, parent, blocks):
        # table properties
        cols = 0
        current_col = 0
        current_row = 0

        # starting divs
        div = etree.SubElement(parent, "div")
        div.set("class", "callout-content")
        row = etree.SubElement(div, "div")
        row.set("class", "test")

        loop = True
        block_i = 0
        while loop:
            # get first block
            block = blocks.pop(0)

            # process first block
            block_i += 1
            if block_i == 1:
                # get first two lines
                lines = block.split("\n")
                line = lines[0]
                # naive counting of cols
                # only format supported: | a | b | --> cols = count(|) - 1
                col_sections = [x.strip() for x in line.split("|") if x.strip() != ""]
                cols = len(col_sections)

                # combine all remaining lines into one string again
                block = "\n".join(lines[2:])

            # foreach block
            sections = block.split("|")
            for section in sections:
                current_col += 1
                if section.strip() != "":
                    if row is None:
                        row = etree.SubElement(div, "div")
                        row.set("class", "test")
                    self.parser.parseChunk(row, section)

                # move to new row
                if current_col > cols:
                    current_row += 1
                    current_col = 0
                    row = None

            # get more blocks?
            if current_col == 1:
                # no more content expected, exit
                loop = False
            else:
                print("continued block", block_i)

        return True
