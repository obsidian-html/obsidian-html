import regex as re
from ..lib import slugify

# Purpose:
# Allows us to get a subsection of a markdown file based on header title
# If a h1 header is given, all the content from that header until the next h1 will be returned.
#
# Usage:
#   from .HeaderTree import PrintHeaderTree, convert_markdown_to_header_tree
#   from .lib import slugify
#   header_id = slugify("My Header Name")
#   header_dict, root_element = convert_markdown_to_header_tree(markdown_content_as_string)
#   print(PrintHeaderTree(header_dict[header_id]))


def _newElement():
    return {"level": 0, "title": "", "md-title": "", "content": [], "parent": None}


def PrintHeaderTree(root_element):
    page = []

    if root_element["level"] > 0:
        page.append(root_element["level"] * "#" + " " + root_element["title"])

    for element in root_element["content"]:
        if type(element) is dict:
            page.append(PrintHeaderTree(element))
        else:
            page.append(element)
    return "\n".join(page)


def GetSubHeaderTree(header_tree, header_selector):
    # header_selector can look like this: section1#h3 (which will be different from section2#h3, for example)
    # if false is returned, something went wrong in the parsing step, the caller can decided whether to bug out or to ignore the link

    def recurse_selector(header_tree, header_selector):
        # get md-title for the next block
        if header_selector.count("#") == 0:
            header_element = header_selector
            new_header_selector = ""
        else:
            header_element, new_header_selector = header_selector.split("#", 1)

        md_title = slugify(header_element)

        # find tree element that matches md_title
        result = recurse_tree(header_tree, md_title)
        if result is None:
            print(f"ERROR: header with title {md_title} was not found")
            return False

        header_tree = result

        # if no new header selector just return the current header_tree
        if new_header_selector == "":
            return header_tree

        # else we loop again
        return recurse_selector(header_tree, new_header_selector)

    def recurse_tree(header_tree, md_title):
        # return the tree itself if it has the correct title
        if header_tree["md-title"] == md_title:
            return header_tree

        # go through the children to find it
        for child in header_tree["content"]:
            if isinstance(child, dict) and "md-title" in child.keys():
                result = recurse_tree(child, md_title)
                if result is not None:
                    return result

        # none found
        return None

    return recurse_selector(header_tree, header_selector)


def convert_markdown_to_header_tree(code):
    lines = code.split("\n")
    current_element = _newElement()
    root_element = current_element
    header_dict = {}

    for i, line in enumerate(lines):
        if len(line) < 2 or line[0] != "#":
            if len(current_element["content"]) == 0 and len(line.strip()) == 0:
                continue
            current_element["content"].append(line)
            continue

        # First char == '#', see if the string makes a header
        looking_for_space = True
        level = 0
        for i, char in enumerate(line):
            if looking_for_space is True and char == "#":
                level += 1
                continue
            if looking_for_space is True and char == " ":
                looking_for_space = False

                # no string after '[#]* ' makes an invalid header, discard
                if len(line) < i:
                    break

                # Header found
                new_element = _newElement()
                new_element["level"] = level
                new_element["title"] = line[i + 1 : len(line)]
                md_title = slugify(new_element["title"])

                if md_title in header_dict.keys():
                    i = 1
                    while (md_title + "_" + str(i)) in header_dict.keys():
                        i += 1
                    md_title = md_title + "_" + str(i)
                new_element["md-title"] = md_title

                # Move up in the tree until both levels are equal, or current_element['level'] is higher than level
                while level < current_element["level"]:
                    current_element = current_element["parent"]
                if level > current_element["level"]:
                    # add to children of current_element
                    current_element["content"].append(new_element)
                    new_element["parent"] = current_element
                elif level == current_element["level"]:
                    # add to children of parent of current_element
                    current_element["parent"]["content"].append(new_element)
                    new_element["parent"] = current_element["parent"]

                # Add to header_dict for easy retrieval
                header_dict[new_element["md-title"]] = new_element

                # Iterate
                current_element = new_element
    return header_dict, root_element


def get_referenced_block(reference, contents, rel_path_str):
    """This function will look in the contents of rel_path_str,
    for the block that is tagged with reference `reference`,  https://help.obsidian.md/Linking+notes+and+files/Internal+links#Link+to+a+block+in+a+note
    and return only the content of that block.
    """
    chunks = []
    current_chunk = ""
    last_line = ""
    for line in contents.split("\n"):
        if line.strip() == "":
            # return chunk if reference is found
            if reference == last_line.strip().rsplit(" ", maxsplit=1)[-1]:  # reference always has to be seperated by at least 1 space and end with a newline and be on the last line of a paragraph
                clean_chunk = re.sub(r"(?<=\s|^)(\^\S*?)(?=$|\n)", "", current_chunk.strip())  # we want to get a non-empty chunk, the reference itself does not count as "non-empty", so remove this
                if clean_chunk == "":
                    clean_chunk = re.sub(r"(?<=\s|^)(\^\S*?)(?=$|\n)", "", chunks[-1].strip())  # current chunk is empty, get last non-empty one and remove the reference from the end
                return clean_chunk

            # add current_chunk to chunk list as long as it is not empty
            if current_chunk.strip() != "":
                chunks.append(current_chunk)

            # start a new chunk
            current_chunk = ""
            last_line = ""
        else:
            # add on to current chunk
            current_chunk += line
            last_line = line

    # When the referenced block ends on the last line, this block will be reached
    if reference == last_line.strip().split(" ")[-1]:
        clean_chunk = re.sub(r"(?<=\s|^)(\^\S*?)(?=$|\n)", "", current_chunk.strip())
        if clean_chunk == "":
            clean_chunk = re.sub(r"(?<=\s|^)(\^\S*?)(?=$|\n)", "", chunks[-1].strip())
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
