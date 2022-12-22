from functools import cache

from ..lib import OpenIncludedFile

def get_side_pane_html(pb, pane_id, node):
    ''' This function gets the HTML for either the left or right pane '''

    if not pb.gc(f'toggles/features/side_pane/{pane_id}/enabled'):
        return ''

    content = get_side_pane_content(pb, pane_id, node)
    template = OpenIncludedFile(f'html/templates/{pane_id}.html')
    template = template.replace('{content}', content)

    return template

def get_side_pane_content(pb, pane_id, node):

    content_selector = pb.gc(f'toggles/features/side_pane/{pane_id}/contents')

    if (content_selector == 'toc'):
        return ''

    if (content_selector == 'tag_tree'):
        if 'tags_page_html' not in pb.jars.keys():
            raise Exception('Make sure that you have enabled the feature create_index_from_tags and that it isnt used as the homepage! tags_page_html not found in jars')
        return '<div class="tags-pane-content">' + pb.jars['tags_page_html'] + '</div>'

    if (content_selector == 'dir_tree'):
        pb.EnsureTreeObj()
        dir_list = pb.treeobj.BuildIndex(current_page=node['url'])
        return dir_list

    return ''


def get_side_pane_id_by_content_selector(pb, content_selector):
    # no side panes available when no documentation layout is selected
    if (pb.gc(f'toggles/features/styling/layout') in ['tabs', 'no_tabs', 'minimal']):
        return ''
        
    if (content_selector == pb.gc(f'toggles/features/side_pane/left_pane/contents')):
        if (pb.gc(f'toggles/features/side_pane/left_pane/enabled')):
            return 'left_pane_content'
        else:
            return ''
    if (content_selector == pb.gc(f'toggles/features/side_pane/right_pane/contents')):
        if (pb.gc(f'toggles/features/side_pane/right_pane/enabled')):
            return 'right_pane_content'
        else:
            return ''
    return ''
        
@cache
def gc_add_toc_when_missing(pb):
    depr = pb.gc('toggles/features/styling/toc_pane')
    if depr != '<DEPRECATED>':
        return str(int(depr))

    res = pb.gc('toggles/features/table_of_contents/add_toc_when_missing')
    return str(int(res))
    
