"""
Footnotes Extension for Python-Markdown
=======================================

Based on https://github.com/Python-Markdown/markdown/blob/master/markdown/extensions/footnotes.py
Added inline footnote functionality

"""
from markdown.extensions import Extension
from markdown.blockprocessors import BlockProcessor
from markdown.inlinepatterns import InlineProcessor
from markdown.treeprocessors import Treeprocessor
from markdown.postprocessors import Postprocessor
from markdown import util
from collections import OrderedDict
import re
import copy
import xml.etree.ElementTree as etree
import base64

FN_BACKLINK_TEXT = util.STX + "zz1337820767766393qq" + util.ETX
NBSP_PLACEHOLDER = util.STX + "qq3936677670287331zz" + util.ETX
RE_REF_ID = re.compile(r"(fnref)(\d+)")


class FootnoteExtension(Extension):
    """Footnote Extension."""

    def __init__(self, **kwargs):
        """Setup configs."""

        self.config = {
            "PLACE_MARKER": ["///Footnotes Go Here///", "The text string that marks where the footnotes go"],
            "UNIQUE_IDS": [False, "Avoid name collisions across " "multiple calls to reset()."],
            "BACKLINK_TEXT": ["&#8617;", "The text string that links from the footnote " "to the reader's place."],
            "SUPERSCRIPT_TEXT": ["{}", "The text string that links from the reader's place " "to the footnote."],
            "BACKLINK_TITLE": [
                "Jump back to footnote %d in the text",
                "The text string used for the title HTML attribute " "of the backlink. %d will be replaced by the " "footnote number.",
            ],
            "SEPARATOR": [":", "Footnote separator."],
        }
        super().__init__(**kwargs)

        # In multiple invocations, emit links that don't get tangled.
        self.unique_prefix = 0
        self.found_refs = {}
        self.used_refs = set()
        self.inc = 0
        self.replacement_inc = 0

        self.reset()

    def extendMarkdown(self, md):
        """Add pieces to Markdown."""
        md.registerExtension(self)
        self.parser = md.parser
        self.md = md
        # Insert a blockprocessor before ReferencePreprocessor
        md.parser.blockprocessors.register(FootnoteBlockProcessor(self), "footnote", 17)

        # Insert an inline pattern before ImageReferencePattern
        FOOTNOTE_RE = r"\[\^([^\]]*)\]"  # blah blah [^1] blah
        md.inlinePatterns.register(FootnoteInlineProcessor(FOOTNOTE_RE, self), "footnote", 175)

        FOOTNOTE_RE_INLINE = r"\^\[([^\]]*)\]"  # blah blah ^[inline footnote] blah
        md.inlinePatterns.register(FootnoteInlineProcessor(FOOTNOTE_RE_INLINE, self, inline_footnote_parser=True), "footnote2", 174)

        # Insert a tree-processor that would actually add the footnote div
        # This must be before all other treeprocessors (i.e., inline and
        # codehilite) so they can run on the the contents of the div.
        md.treeprocessors.register(FootnoteTreeprocessor(self), "footnote", 50)

        # Insert a tree-processor that will run after inline is done.
        # In this tree-processor we want to check our duplicate footnote tracker
        # And add additional backrefs to the footnote pointing back to the
        # duplicated references.
        md.treeprocessors.register(FootnotePostTreeprocessor(self), "footnote-duplicate", 15)

        # Insert a postprocessor after amp_substitute processor
        md.postprocessors.register(FootnotePostprocessor(self), "footnote", 25)

    def reset(self):
        """Clear footnotes on reset, and prepare for distinct document."""
        self.footnotes = []
        self.footnotes_new = OrderedDict()
        self.unique_prefix += 1
        self.found_refs = {}
        self.used_refs = set()
        self.codeblocks = {}
        self.codelines = {}

    def unique_ref(self, reference, found=False):
        """Get a unique reference if there are duplicates."""
        if not found:
            return reference

        original_ref = reference
        while reference in self.used_refs:
            ref, rest = reference.split(self.get_separator(), 1)
            m = RE_REF_ID.match(ref)
            if m:
                reference = "%s%d%s%s" % (m.group(1), int(m.group(2)) + 1, self.get_separator(), rest)
            else:
                reference = "%s%d%s%s" % (ref, 2, self.get_separator(), rest)

        self.used_refs.add(reference)
        if original_ref in self.found_refs:
            self.found_refs[original_ref] += 1
        else:
            self.found_refs[original_ref] = 1
        return reference

    def findFootnotesPlaceholder(self, root):
        """Return ElementTree Element that contains Footnote placeholder."""

        def finder(element):
            for child in element:
                if child.text:
                    if child.text.find(self.getConfig("PLACE_MARKER")) > -1:
                        return child, element, True
                if child.tail:
                    if child.tail.find(self.getConfig("PLACE_MARKER")) > -1:
                        return child, element, False
                child_res = finder(child)
                if child_res is not None:
                    return child_res
            return None

        res = finder(root)
        return res

    def StripCodeSections(self, block):
        """(Temporarily) Remove codeblocks/-lines so that they are not altered in all the conversions. Placeholders are inserted."""
        codeblocks = re.findall("^```([\s\S]*?)```[\s]*?$", block, re.MULTILINE)
        for i, codeblock in enumerate(codeblocks):
            rid = self.getReplacementId()
            self.codeblocks[rid] = codeblock
            block = block.replace("```" + codeblock + "```", f"%%%codeblock-placeholder-{rid}%%%")

        codelines = re.findall("`(.*?)`", block)
        for i, codeline in enumerate(codelines):
            rid = self.getReplacementId()
            self.codelines[rid] = codeline
            block = block.replace("`" + codeline + "`", f"%%%codeline-placeholder-{rid}%%%")

        return block

    def RestoreCodeSections(self, block):
        """Undo the action of StripCodeSections."""
        for rid in self.codeblocks.keys():
            value = self.codeblocks[rid]
            block = block.replace(f"%%%codeblock-placeholder-{rid}%%%", f"```{value}```\n")
        for rid in self.codelines.keys():
            value = self.codelines[rid]
            block = block.replace(f"%%%codeline-placeholder-{rid}%%%", f"`{value}`")
        return block

    def getId(self):
        self.inc += 1
        return self.inc

    def getReplacementId(self):
        self.replacement_inc += 1
        return self.replacement_inc

    def getKey(self, name):
        message = name
        message_bytes = message.encode("ascii")
        base64_bytes = base64.b64encode(message_bytes)
        base64_message = base64_bytes.decode("ascii")
        key = base64_message

        # i = 0
        # while key in self.footnotes.keys():
        #     key = base64_message + str(i)

        return key

    def setFootnote(self, name, text):
        """Store a footnote for later retrieval."""
        i, fn = self.getFootnoteByName(name)
        if fn is None:
            raise Exception("Expected footnote definition")
        self.footnotes[i]["text"] = self.RestoreCodeSections(text)

    def setFootnoteOrderLookup(self, name):
        i, fn = self.getFootnoteByName(name)
        if fn is None:
            self.footnotes.append({"id": self.getId(), "name": name, "text": None})
            return self.footnotes[-1]
        return fn

    def getFootnoteByName(self, name):
        for i, fn in enumerate(self.footnotes):
            if fn["name"] == name:
                return (i, fn)
        return (None, None)

    def get_separator(self):
        """Get the footnote separator."""
        return self.getConfig("SEPARATOR")

    def makeFootnoteId(self, id):
        """Return footnote link id."""
        if self.getConfig("UNIQUE_IDS"):
            return "fn%s%d-%s" % (self.get_separator(), self.unique_prefix, id)
        else:
            return "fn{}{}".format(self.get_separator(), id)

    def makeFootnoteRefId(self, id, found=False):
        """Return footnote back-link id."""
        if self.getConfig("UNIQUE_IDS"):
            return self.unique_ref("fnref%s%d-%s" % (self.get_separator(), self.unique_prefix, id), found)
        else:
            return self.unique_ref("fnref{}{}".format(self.get_separator(), id), found)

    def makeFootnotesDiv(self, root):
        """Return div of footnotes as et Element."""

        if not list(self.footnotes):
            return None

        div = etree.Element("div")
        div.set("class", "footnote")
        etree.SubElement(div, "hr")
        ol = etree.SubElement(div, "ol")
        surrogate_parent = etree.Element("div")

        # Backward compatibility with old '%d' placeholder
        backlink_title = self.getConfig("BACKLINK_TITLE").replace("%d", "{}")

        for index, fn in enumerate(self.footnotes):
            li = etree.SubElement(ol, "li")
            li.set("id", self.makeFootnoteId(fn["id"]))

            # Parse footnote with surrogate parent as li cannot be used.
            # List block handlers have special logic to deal with li.
            # When we are done parsing, we will copy everything over to li.
            if fn["text"] is not None:
                text = self.RestoreCodeSections(fn["text"])

                # change code blocks so the newlines are not stripped
                text = convert_codeblocks(text)
                self.parser.parseChunk(surrogate_parent, text)

            for el in list(surrogate_parent):
                li.append(el)
                surrogate_parent.remove(el)
            backlink = etree.Element("a")
            backlink.set("href", "#" + self.makeFootnoteRefId(fn["id"]))
            backlink.set("class", "footnote-backref")
            backlink.set("title", backlink_title.format(index))
            backlink.text = FN_BACKLINK_TEXT

            if len(li):
                node = li[-1]
                if node.tag == "p":
                    node.text = node.text + NBSP_PLACEHOLDER
                    node.append(backlink)
                else:
                    p = etree.SubElement(li, "p")
                    p.append(backlink)
        return div


class FootnoteBlockProcessor(BlockProcessor):
    """Find all footnote references and store for later use."""

    RE = re.compile(r"^[ ]{0,3}\[\^([^\]]*)\]:[ ]*(.*)$", re.MULTILINE)
    RE_INLINE = re.compile(r"^.*\^\[([^\]]*)\]*(.*)$", re.MULTILINE)

    def __init__(self, footnotes):
        super().__init__(footnotes.parser)
        self.footnotes = footnotes

    def test(self, parent, block):
        return True

    def run(self, parent, blocks):
        """Find, set, and remove footnote definitions."""
        block = blocks.pop(0)
        block = self.footnotes.StripCodeSections(block)

        # add inline references to lookup
        # we use the inline usages because these are ordered as the id's should be
        # =================================================
        FOOTNOTE_RE = re.compile(r"\[\^([^\]]*)\]", re.MULTILINE)
        m = FOOTNOTE_RE.findall(block)
        if m:
            for item in m:
                self.footnotes.setFootnoteOrderLookup(item)

        FOOTNOTE_RE = re.compile(r"\^\[([^\]]*)\]", re.MULTILINE)
        m = FOOTNOTE_RE.findall(block)
        if m:
            for item in m:
                self.footnotes.setFootnoteOrderLookup(item)

        # handle the footnote descriptions
        # =================================================
        m = self.RE.search(block)
        if m:
            # get text, e.g. [^bla] --> name = "bla"
            name = m.group(1)
            fn_blocks = [m.group(2)]

            # Handle rest of block
            therest = block[m.end() :].lstrip("\n")
            m2 = self.RE.search(therest)
            if m2:
                # Another footnote exists in the rest of this block.
                # Any content before match is continuation of this footnote, which may be lazily indented.
                before = therest[: m2.start()].rstrip("\n")
                fn_blocks[0] = "\n".join([fn_blocks[0], self.detab(before)]).lstrip("\n")
                # Add back to blocks everything from beginning of match forward for next iteration.
                blocks.insert(0, therest[m2.start() :])
            else:
                # All remaining lines of block are continuation of this footnote, which may be lazily indented.
                fn_blocks[0] = "\n".join([fn_blocks[0], self.detab(therest)]).strip("\n")

                # Check for child elements in remaining blocks.
                fn_blocks.extend(self.detectTabbed(blocks))

            footnote = "\n\n".join(fn_blocks)

            self.footnotes.setFootnote(name, footnote.rstrip())
            block = self.footnotes.RestoreCodeSections(block)

            if block[: m.start()].strip():
                # Add any content before match back to blocks as separate block
                blocks.insert(0, block[: m.start()].rstrip("\n"))
            return True

        # fetch inline footnotes, these will be deleted by the inline parser
        # we have this code here because we need to set the footnotes so that we have them for when the footnotes are created at the bottom of the page.
        m = self.RE_INLINE.search(block)
        if m:
            # get text, e.g. bla ^[this is my inline footnote] bla --> text = "this is my inline footnote"
            text = m.group(1)

            # create footnote
            self.footnotes.setFootnote(text, text)  # todo: name can conflict in this case

        # No (non-inline) footnote match. Restore block.
        block = self.footnotes.RestoreCodeSections(block)
        blocks.insert(0, block)
        return False

    def detectTabbed(self, blocks):
        """Find indented text and remove indent before further processing.

        Returns: a list of blocks with indentation removed.
        """
        fn_blocks = []
        while blocks:
            if blocks[0].startswith(" " * 4):
                block = blocks.pop(0)
                # Check for new footnotes within this block and split at new footnote.
                m = self.RE.search(block)
                if m:
                    # Another footnote exists in this block.
                    # Any content before match is continuation of this footnote, which may be lazily indented.
                    before = block[: m.start()].rstrip("\n")
                    fn_blocks.append(self.detab(before))
                    # Add back to blocks everything from beginning of match forward for next iteration.
                    blocks.insert(0, block[m.start() :])
                    # End of this footnote.
                    break
                else:
                    # Entire block is part of this footnote.
                    fn_blocks.append(self.detab(block))
            else:
                # End of this footnote.
                break
        return fn_blocks

    def detab(self, block):
        """Remove one level of indent from a block.

        Preserve lazily indented blocks by only removing indent from indented lines.
        """
        lines = block.split("\n")
        for i, line in enumerate(lines):
            if line.startswith(" " * 4):
                lines[i] = line[4:]
        return "\n".join(lines)


class FootnoteInlineProcessor(InlineProcessor):
    """InlinePattern for footnote markers in a document's body text."""

    def __init__(self, pattern, footnotes, inline_footnote_parser=False):
        super().__init__(pattern)
        self.footnotes = footnotes
        self.inline_footnote_parser = inline_footnote_parser

    def handleMatch(self, m, data):
        name = m.group(1)
        footnote_id = None

        i, fn = self.footnotes.getFootnoteByName(name)
        if fn is not None:
            footnote_id = fn["id"]

        if footnote_id is None:
            return None, None, None

        sup = etree.Element("sup")
        a = etree.SubElement(sup, "a")
        sup.set("id", self.footnotes.makeFootnoteRefId(str(footnote_id), found=True))
        a.set("href", "#" + self.footnotes.makeFootnoteId(str(footnote_id)))
        a.set("class", "footnote-ref")
        a.text = str(footnote_id)
        return sup, m.start(0), m.end(0)


class FootnotePostTreeprocessor(Treeprocessor):
    """Amend footnote div with duplicates."""

    def __init__(self, footnotes):
        self.footnotes = footnotes

    def add_duplicates(self, li, duplicates):
        """Adjust current li and add the duplicates: fnref2, fnref3, etc."""
        for link in li.iter("a"):
            # Find the link that needs to be duplicated.
            if link.attrib.get("class", "") == "footnote-backref":
                ref, rest = link.attrib["href"].split(self.footnotes.get_separator(), 1)
                # Duplicate link the number of times we need to
                # and point the to the appropriate references.
                links = []
                for index in range(2, duplicates + 1):
                    sib_link = copy.deepcopy(link)
                    sib_link.attrib["href"] = "%s%d%s%s" % (ref, index, self.footnotes.get_separator(), rest)
                    links.append(sib_link)
                    self.offset += 1
                # Add all the new duplicate links.
                el = list(li)[-1]
                for link in links:
                    el.append(link)
                break

    def get_num_duplicates(self, li):
        """Get the number of duplicate refs of the footnote."""
        fn, rest = li.attrib.get("id", "").split(self.footnotes.get_separator(), 1)
        link_id = "{}ref{}{}".format(fn, self.footnotes.get_separator(), rest)
        return self.footnotes.found_refs.get(link_id, 0)

    def handle_duplicates(self, parent):
        """Find duplicate footnotes and format and add the duplicates."""
        for li in list(parent):
            # Check number of duplicates footnotes and insert
            # additional links if needed.
            count = self.get_num_duplicates(li)
            if count > 1:
                self.add_duplicates(li, count)

    def run(self, root):
        """Crawl the footnote div and add missing duplicate footnotes."""
        self.offset = 0
        for div in root.iter("div"):
            if div.attrib.get("class", "") == "footnote":
                # Footnotes should be under the first ordered list under
                # the footnote div.  So once we find it, quit.
                for ol in div.iter("ol"):
                    self.handle_duplicates(ol)
                    break


class FootnoteTreeprocessor(Treeprocessor):
    """Build and append footnote div to end of document."""

    def __init__(self, footnotes):
        self.footnotes = footnotes

    def run(self, root):
        footnotesDiv = self.footnotes.makeFootnotesDiv(root)
        if footnotesDiv is not None:
            result = self.footnotes.findFootnotesPlaceholder(root)
            if result:
                child, parent, isText = result
                ind = list(parent).index(child)
                if isText:
                    parent.remove(child)
                    parent.insert(ind, footnotesDiv)
                else:
                    parent.insert(ind + 1, footnotesDiv)
                    child.tail = None
            else:
                root.append(footnotesDiv)


class FootnotePostprocessor(Postprocessor):
    """Replace placeholders with html entities."""

    def __init__(self, footnotes):
        self.footnotes = footnotes

    def run(self, text):
        text = text.replace(FN_BACKLINK_TEXT, self.footnotes.getConfig("BACKLINK_TEXT"))
        return text.replace(NBSP_PLACEHOLDER, "&#160;")


def makeExtension(**kwargs):  # pragma: no cover
    """Return an instance of the FootnoteExtension"""
    return FootnoteExtension(**kwargs)


def convert_codeblocks(text):
    mode = False
    acc = []
    for line in text.split("\n"):
        if line.startswith("```"):
            if mode is False:
                acc.append("")
            mode = not mode
            continue
        if mode:
            acc.append("    " + line)
        else:
            acc.append(line)

    acc = "\n".join(acc)
    return acc
