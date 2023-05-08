from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

import re
from pathlib import Path

DataviewRegexBegin = re.compile(r"^\ *\`\`\`\ *dataview")
DataviewRegexEnd = re.compile(r"^\ *\`\`\`")
DataviewInlineRegexRepl = re.compile(r"(?<=[^\`\n])\`\${0,1}=([^\`]*?\`)")

# globals
GLOBAL_COUNTERS = {"line": 0, "table": 0}
GLOBAL_DATAVIEW_ELEMENTS = None


class DataviewExtension(Extension):
    def __init__(self, **kwargs):
        self.config = {
            "note_path": ["not set", "Path to the note relative to the vault"],
            "dataview_export_folder": ["not set", "Absolute path to the dataview export folder"],
        }
        super(DataviewExtension, self).__init__(**kwargs)

    """ Add source code hilighting to markdown codeblocks. """

    def extendMarkdown(self, md):
        md.preprocessors.register(DataviewPreprocessor(self, md), "dataview", 35)
        md.registerExtension(self)


def makeExtension(**kwargs):
    return DataviewExtension(**kwargs)


class DataviewPreprocessor(Preprocessor):
    def __init__(self, extension, md=None):
        self.md = md
        self.extension = extension

    def run(self, lines):
        new_lines = []

        m_start = None
        m_end = None
        in_dataview_code = False

        for line in lines:
            m_start = None
            m_end = None

            if not in_dataview_code:
                # Match `=<query>` and `$=<query>` lines
                # -----------------------------------------------------------------------
                match = DataviewInlineRegexRepl.search(line)
                if match:
                    self.load_dataview_elements()
                    new_line = DataviewInlineRegexRepl.sub(replace_inline_block, line)
                    new_lines.append(new_line)
                    continue

                # Match ``` dataview blocks
                # -----------------------------------------------------------------------
                m_start = DataviewRegexBegin.match(line)
                if m_start:
                    self.load_dataview_elements()

                    in_dataview_code = True
                    # Add in dataview table
                    new_lines.append(f'<div class="dataview">\n{get_next("table")}')
                else:
                    new_lines.append(line)

            else:
                m_end = DataviewRegexEnd.match(line)
                if m_end:
                    in_dataview_code = False
                    new_lines.append("</div>")
                    new_lines.append("")
                else:
                    # new_lines.append(line)
                    pass

        return new_lines

    # def get_dataview(self, key, counter, dataview_elements):
    #     if dataview_elements is None:
    #         dataview_elements = self.get_dataview_elements()

    #     dataview_element = dataview_elements[key][counter]

    #     return (dataview_element, dataview_elements)

    def load_dataview_elements(self):
        global GLOBAL_DATAVIEW_ELEMENTS
        if GLOBAL_DATAVIEW_ELEMENTS is not None:
            return

        # get note contents and convert to soup
        note_path = self.extension.getConfig("note_path")
        dataview_export_folder = self.extension.getConfig("dataview_export_folder")
        path = Path(f"{dataview_export_folder}/{note_path}").with_suffix(".md.html")
        print(path)

        with open(path, "r", encoding="utf-8") as f:
            html = f.read().replace('.md"', '.html"').replace('href="', 'href="/')

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        # fill var
        GLOBAL_DATAVIEW_ELEMENTS = {}

        # get blocks (appear as tables)
        GLOBAL_DATAVIEW_ELEMENTS["table"] = [str(x) for x in soup.find_all("table", {"class": "dataview"})]
        print("dataview tables: ", len(GLOBAL_DATAVIEW_ELEMENTS["table"]))

        # get inline queries
        GLOBAL_DATAVIEW_ELEMENTS["line"] = [str(x) for x in soup.select(".dataview-inline-query")]
        print("dataview lines: ", len(GLOBAL_DATAVIEW_ELEMENTS["line"]))


def get_next(key):
    global GLOBAL_COUNTERS
    global GLOBAL_DATAVIEW_ELEMENTS

    # get counter then increment
    i = GLOBAL_COUNTERS[key]
    GLOBAL_COUNTERS[key] += 1

    # return element
    return GLOBAL_DATAVIEW_ELEMENTS[key][i]


def replace_inline_block(match_obj):
    print(match_obj.group(0))
    val = get_next("line")
    print("--->", val)
    return val
