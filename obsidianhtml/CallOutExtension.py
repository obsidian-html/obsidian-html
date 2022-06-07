from markdown.extensions import Extension
from markdown.blockprocessors import BlockProcessor
import re
import xml.etree.ElementTree as etree

from .SharedResources import shared_obsidian_svgs

def makeExtension(**kwargs):  # pragma: no cover
    return CallOutExtension(**kwargs)

class CallOutExtension(Extension):
    def extendMarkdown(self, md):
        md.parser.blockprocessors.register(CallOutBlockProcessor(md.parser), 'CallOutExtension', 175)

class CallOutBlockProcessor(BlockProcessor):
    RE_FENCE_START = r'^> *\[\!.*?].*?\n' 

    def __init__(self, parser):
        """Initialization."""

        super().__init__(parser)
    
        # load svgs
        self.svgs = shared_obsidian_svgs
        
    def test(self, parent, block):
        return re.match(self.RE_FENCE_START, block)

    def run(self, parent, blocks):
        #original_block = blocks[0] 
        #blocks[0] = re.sub(self.RE_FENCE_START, '', blocks[0])

        block = blocks.pop(0)

        chunk = ''
        for i, line in enumerate(block.split('\n')):
            # first line has information for formatting, extract this
            # and use this space to init the callout div and title div
            if i == 0:
                # get information on callout from the first line
                data = self.parseHeader(line)
                #print(data)

                # create callout div
                div = etree.SubElement(parent, 'div')

                # add classes to callout div
                classlist = f'callout callout-{data["call-out-class"]} active' # class active will be removed on page load if js is enabled
                if data['folded']:
                    classlist += ' ' + 'callout-folded'
                div.set('class', classlist)
                div.set('rasa', '1')

                # add the titlebar subdiv
                title = etree.SubElement(div, 'div')
                title.set('class', 'callout-title')
                if data['folded']:
                    title.set('onclick', f'toggle(this.parentElement)')

                # get the svg for the title bar icon
                svg_name = data['call-out-class']
                if svg_name not in self.svgs.keys():
                    svg_name = 'default'

                # add title bar icon
                title_icon = etree.SubElement(title, 'div')
                title_icon.set('class', 'callout-title-icon')
                title_icon.text = self.svgs[svg_name] + '\n'

                # add title bar header
                title_name = etree.SubElement(title, 'div')
                title_name.set('class', 'callout-title-name')
                title_name.text = data['title'] + '\n'

                # add fold svg 
                if data['folded']:
                    fold = etree.SubElement(title, 'div')
                    fold.set('class', 'callout-title-fold')
                    fold.text = self.svgs['fold']

                # add data div
                data_div = etree.SubElement(div, 'div')
                data_div.set('class', 'callout-content')

                continue

            # remove leading >
            if line.startswith('>'):
                line = line[1:]
            line = line.lstrip()

            if line == '':
                # compile chunk
                self.parser.parseChunk(data_div, chunk)

                # setup new chunk
                chunk = ''
                continue

            chunk += line + '\n'

        if chunk != '':
            self.parser.parseChunk(data_div, chunk)

        return True 

    def parseHeader(self, line):
        # output
        folded = False

        # first parse line into bracket_content and tail
        start_bracket = False
        end_bracket = False
        bracket_content = ''
        tail = ''
        for ch in line:
            if start_bracket == False and ch == '[':
                start_bracket = True
                continue
            if start_bracket == True:
                if ch == ']':
                    end_bracket = True 
                    continue
                if ch == '!' and end_bracket == False:
                    continue
                if end_bracket == False:
                    bracket_content += ch
                    continue
            if end_bracket == True:
                tail += ch

        # read tail to get configuration
        if tail.startswith('-'):
            folded = True
            tail = tail[1:]

        tail = tail.lstrip()
        if tail != '':
            title = tail
        else:
            title = bracket_content.capitalize()
        
        return {'call-out-class': bracket_content.lower(), 'title': title, 'folded': folded }
            
