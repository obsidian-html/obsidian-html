import regex as re                   # regex string finding/replacing
import urllib.parse         # convert link characters like %

# -- [3] Convert Obsidian type img links to proper md image links
# Further conversion will be done in the block below
def obs_img_to_md_img(pb, page):
    for link in re.findall("(?<=\!\[\[)(.*?)(?=\]\])", page):
        if '|' in link:
            parts = link.split('|')
            l = parts.pop(0)
            alias = '|'.join(parts)
            new_link = f'![{alias}]('+urllib.parse.quote(l)+')'
        else:
            new_link = '![]('+urllib.parse.quote(link)+')'

        # Obsidian page inclusions use the same tag...
        # Skip if we don't match image suffixes. Inclusions are handled at the end.
        l = link.split('|')[0]
        if len(l.split('.')) == 1 or l.split('.')[-1].lower() not in pb.gc('included_file_suffixes', cached=True):
            new_link = f'<inclusion href="{l}" />'

        safe_link = re.escape('![['+link+']]')
        page = re.sub(safe_link, new_link, page)
        
    return page


def md_to_html(pb, page, rel_dst_path):
    import markdown
    from ..markdown_extensions.CallOutExtension import CallOutExtension
    from ..markdown_extensions.DataviewExtension import DataviewExtension
    from ..markdown_extensions.MermaidExtension import MermaidExtension
    from ..markdown_extensions.CustomTocExtension import CustomTocExtension
    from ..markdown_extensions.EraserExtension import EraserExtension
    from ..markdown_extensions.FootnoteExtension import FootnoteExtension
    from ..markdown_extensions.FormattingExtension import FormattingExtension
    from ..markdown_extensions.EmbeddedSearchExtension import EmbeddedSearchExtension
    from ..markdown_extensions.CodeWrapperExtension import CodeWrapperExtension
    from ..markdown_extensions.AdmonitionExtension import AdmonitionExtension
    from ..markdown_extensions.BlockLinkExtension import BlockLinkExtension

    extensions = [
        'abbr', 'attr_list', 'def_list', 
        'fenced_code', 'tables',
        'md_in_html', FootnoteExtension(), FormattingExtension(), 
        'codehilite', 
        CustomTocExtension(), MermaidExtension(), CallOutExtension(), 'pymdownx.arithmatex'
    ]

    extension_configs = {
        'codehilite': {
            'linenums': False
        },
        'pymdownx.arithmatex': {
            'generic': True
        }
    }

    if pb.gc('toggles/features/dataview/enabled'):
        extensions.append('dataview')
        extension_configs['dataview'] = {
            'note_path': rel_dst_path,
            'dataview_export_folder': pb.paths['dataview_export_folder']
        }
        
    if pb.gc('toggles/features/eraser/enabled'):
        extensions.append(EraserExtension())

    if pb.gc('toggles/features/embedded_search/enabled'):
        extensions.append(EmbeddedSearchExtension())

    extensions.append(CodeWrapperExtension())
    extensions.append(AdmonitionExtension())
    extensions.append(BlockLinkExtension())

    html_body = markdown.markdown(page, extensions=extensions, extension_configs=extension_configs)
    return html_body

def obs_callout_to_markdown_callout(page, strict_line_breaks=False):
    linebreak = '   \n'
    if strict_line_breaks: 
        linebreak = '\n'

    def convert_block(block):
        # first line contains all the data, extract this
        fl = block[0]
        callout_type_name = fl.split('[')[1].split(']')[0][1:]

        tail = fl.split(']', 1)[1]
        foldable = False
        folded = False
        if len(tail) > 0:
            if tail[0] == '-':
                foldable = True
                folded = True
            if tail[0] == '+':
                foldable = True
                folded = False
        title = tail[1:].strip()

        # build first line of output
        fold_symbol = ''
        if foldable:
            fold_symbol = '!'
            if folded:
                fold_symbol = '?'
        if title:
            title = f" **{title}**"
        output = f">{fold_symbol} {callout_type_name.upper()}:{title}"

        # Add second line to block
        if len(block) > 1:
            sl = block[1][1:].lstrip()
            if re.match(r'^\*\*', sl):
                sl = linebreak + sl
            else:
                sl = ' ' + sl
            output += sl + linebreak
        # Add the rest
        if len(block) > 2:
            for line in block[2:]:
                output += line.rstrip() + linebreak

        return output

    output = []

    # split into blocks
    lines = page.split('\n')
    blocks = []
    cblock = []
    for line in lines:
        if line.strip() == '':
            blocks.append(cblock)
            cblock = []
            continue
        cblock.append(line)
    if len(cblock) > 0:
        blocks.append(cblock)

    # parse blocks
    for block in blocks:
        # empty block
        if len(block) == 0:
            output.append('')
            continue
        # obsidian callout
        if re.match(r'^\s*>\s*\[!.*?\]', block[0]):
            output.append(convert_block(block))
            continue
        # normal block
        output += block + ['']
    
    return '\n'.join(output)
