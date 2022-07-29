import regex as re
import yaml
from .lib import slugify

# Purpose:
# Allows us to get a subsection of a markdown file based on header title
# If a h1 header is given, all the content from that header until the next h1 will be returned.
#
# Usage:
#   from .HeaderTree import PrintHeaderTree, ConvertMarkdownToHeaderTree
#   from .lib import slugify
#   header_id = slugify("My Header Name")
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
                    md_title = slugify(new_element['title'])
                    
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

def GetReferencedBlock(reference, contents, rel_path_str):
    chunks = []
    current_chunk = ''
    last_line = ''
    for line in contents.split('\n'):
        if line.strip() == '':
            # return chunk if reference is found
            if reference == last_line.strip().split(' ')[-1]:                                       # reference always has to be seperated by at least 1 space and end with a newline and be on the last line of a paragraph
                clean_chunk = re.sub(r'(?<=\s|^)(\^\S*?)(?=$|\n)', '', current_chunk.strip())       # we want to get a non-empty chunk, the reference itself does not count as "non-empty", so remove this
                if clean_chunk == '':
                    clean_chunk = re.sub(r'(?<=\s|^)(\^\S*?)(?=$|\n)', '', chunks[-1].strip())      # current chunk is empty, get last non-empty one and remove the reference from the end
                return clean_chunk

            # add current_chunk to chunk list as long as it is not empty
            if current_chunk.strip() != '':                                     
                chunks.append(current_chunk)

            # start a new chunk
            current_chunk = ''
            last_line = ''
        else:
            # add on to current chunk
            current_chunk += line
            last_line = line

    # When the referenced block ends on the last line, this block will be reached
    if reference == last_line.strip().split(' ')[-1]:
        clean_chunk = re.sub(r'(?<=\s|^)(\^\S*?)(?=$|\n)', '', current_chunk.strip())
        if clean_chunk == '':
            clean_chunk = re.sub(r'(?<=\s|^)(\^\S*?)(?=$|\n)', '', chunks[-1].strip())
        return clean_chunk

    # No reference found
    return f"Unable to find section #{reference} in {rel_path_str}"


# def FindHeaderTreeKey(key_list, key):
#     # this code will find a key in the key list that is the same as the provided key
#     # with the option for one or more '-' at any location in the provided key relative to
#     # the keys in the keylist 

#     if key in key_list:
#         return key

#     # first try to match keys without -
#     naive_matches = []
#     skey = key.replace('-', '')
#     for k in key_list:
#         if k.replace('-', '') == skey:
#             naive_matches.append(k)

#     if len(naive_matches) == 1:
#         return naive_matches[0]
#     if len(naive_matches) == 0:
#         raise Exception(f"Header {key} not found in list of {key_list}")

#     # more than one match found
#     # wifi-2-4-vs-5-0   wifi-24-vs-50  
#     c = 0
#     for k in naive_matches:
#         for char in k:
#             if char == key[c]:
#                 c += 1
#                 if c == len(key):
#                     return k
#             elif key[c] == '-':
#                 c += 1
#                 if char == key[c]:
#                     c += 1
#                     if c == len(key):
#                         return k
#             else: 
#                 continue
#     raise Exception(f"Header {key} not found in list of {key_list}")
