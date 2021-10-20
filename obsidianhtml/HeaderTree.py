import re
import yaml
from .lib import ConvertTitleToMarkdownId

# Purpose:
# Allows us to get a subsection of a markdown file based on header title
# If a h1 header is given, all the content from that header until the next h1 will be returned.
#
# Usage:
#   from .HeaderTree import PrintHeaderTree, ConvertMarkdownToHeaderTree
#   from .lib import ConvertTitleToMarkdownId
#   header_id = ConvertTitleToMarkdownId("My Header Name")
#   header_dict, root_element = ConvertMarkdownToHeaderTree(markdown_content_as_string)
#   print(PrintHeaderTree(header_dict[header_id]))

def _newElement():
    return {'level': 0, 'title': '', 'md-title': '', 'content': [], 'parent': None}

def PrintHeaderTree(root_element):
    page = []

    if root_element['level'] > 0:
        page.append(root_element['level'] * '#' + ' ' + root_element['title'])

    for element in root_element['content']:
        
        if type(element) is dict:
            page.append(PrintHeaderTree(element))
        else:
            page.append(element)
    return '\n'.join(page)

def ConvertMarkdownToHeaderTree(code):
    lines = code.split('\n')
    current_element = _newElement()
    root_element = current_element
    header_dict = {}

    for i, line in enumerate(lines):
        if len(line) < 2 or line[0] != '#':
            current_element['content'].append(line)
            continue

        # First char == '#', see if the string makes a header
        is_header = True
        looking_for_space = True
        header_formed = False
        level = 0
        for i, char in enumerate(line):
            if looking_for_space == True and char == '#':
                level += 1
                continue
            if looking_for_space == True and char == ' ':
                looking_for_space = False

                # no string after '[#]* ' makes an invalid header, discard
                if len(line) < i:
                    break
                # Header found
                else:
                    new_element = _newElement()
                    new_element['level'] = level
                    new_element['title'] = line[i+1:len(line)]
                    md_title = ConvertTitleToMarkdownId(new_element['title'])
                    
                    if md_title in header_dict.keys():
                        i = 1
                        while (md_title + '_' + str(i)) in header_dict.keys():
                            i += 1 
                        md_title = md_title + '_' + str(i)
                    new_element['md-title'] = md_title

                    # Move up in the tree until both levels are equal, or current_element['level'] is higher than level
                    while level < current_element['level']:
                        current_element = current_element['parent']                
                    if level > current_element['level']:
                        # add to children of current_element
                        current_element['content'].append(new_element)
                        new_element['parent'] = current_element
                    elif level == current_element['level']:
                        # add to children of parent of current_element
                        current_element['parent']['content'].append(new_element)
                        new_element['parent'] = current_element['parent']

                    # Add to header_dict for easy retrieval
                    header_dict[new_element['md-title']] = new_element

                    # Iterate
                    current_element = new_element
    return header_dict, root_element


