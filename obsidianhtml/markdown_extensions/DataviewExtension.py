from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

import re
import string
from pathlib import Path

DataviewRegexBegin = re.compile(r"^\ *\`\`\`\ *dataview")
DataviewRegexEnd = re.compile(r"^\ *\`\`\`")

class DataviewExtension(Extension):
    def __init__(self, **kwargs):
        self.config = {
            'note_path' : ['not set', 'Path to the note relative to the vault'],
            'dataview_export_folder' : ['not set', 'Absolute path to the dataview export folder']
        }
        super(DataviewExtension, self).__init__(**kwargs)

    """ Add source code hilighting to markdown codeblocks. """
    def extendMarkdown(self, md):
        md.preprocessors.register(DataviewPreprocessor(self, md), 'dataview', 35)
        md.registerExtension(self)

def makeExtension(**kwargs): 
    return DataviewExtension(**kwargs)

class DataviewPreprocessor(Preprocessor):
    def __init__(self, extension, md=None):
        self.md = md
        self.extension = extension

    def run(self, lines):
        counter = 0
        dataview_tables = None

        new_lines = []
        
        m_start = None
        m_end = None
        in_dataview_code = False
        is_dataview = False

        for line in lines:
            m_start = None
            m_end = None

            if not in_dataview_code:
                m_start = DataviewRegexBegin.match(line)
                if m_start:
                    in_dataview_code = True
                    # Add in dataview table
                    dataview, dataview_tables = self.get_dataview(counter, dataview_tables)
                    new_lines.append(f'<div class="dataview">\n{dataview}')
                    # Inc
                    counter += 1
                else:
                    new_lines.append(line)

            else:
                m_end = DataviewRegexEnd.match(line)
                if m_end:
                    in_dataview_code = False
                    new_lines.append('</div>')
                    new_lines.append("")
                else:
                    #new_lines.append(line)
                    pass

        return new_lines

    def get_dataview(self, counter, dataview_tables):
        if dataview_tables is None:
            dataview_tables = self.get_dataview_tables()

        dataview_table = dataview_tables[counter]

        return (dataview_table, dataview_tables)
    

    def get_dataview_tables(self):
        note_path = self.extension.getConfig('note_path')
        dataview_export_folder = self.extension.getConfig('dataview_export_folder')
        path = Path(f'{dataview_export_folder}/{note_path}').with_suffix('.md.html')
        print(path)

        with open(path, 'r', encoding='utf-8') as f:
            html = f.read().replace('.md"', '.html"').replace('href="', 'href="/')

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        dataview_tables = [str(x) for x in soup.find_all("table", {"class": "dataview"})]
        return dataview_tables
    

