import regex as re
from pathlib import Path


def convert_markdown_output(md_folder_path, convert_function, arg_dict=None):
    for file in Path(md_folder_path).rglob("*.md"):
        with open(file, "r") as f:
            content = f.read()
        content = convert_function(content, **arg_dict)
        with open(file, "w") as f:
            content = f.write(content)


def obs_callout_to_markdown_callout(page, strict_line_breaks=False):
    linebreak = "   \n"
    if strict_line_breaks:
        linebreak = "\n"

    def convert_block(block):
        # first line contains all the data, extract this
        fl = block[0]
        callout_type_name = fl.split("[")[1].split("]")[0][1:]

        tail = fl.split("]", 1)[1]
        foldable = False
        folded = False
        if len(tail) > 0:
            if tail[0] == "-":
                foldable = True
                folded = True
            if tail[0] == "+":
                foldable = True
                folded = False
        title = tail[1:].strip()

        # build first line of output
        fold_symbol = ""
        if foldable:
            fold_symbol = "!"
            if folded:
                fold_symbol = "?"
        if title:
            title = f" **{title}**"
        output = f">{fold_symbol} {callout_type_name.upper()}:{title}"

        # Add second line to block
        if len(block) > 1:
            sl = block[1][1:].lstrip()
            if re.match(r"^\*\*", sl):
                sl = linebreak + sl
            else:
                sl = " " + sl
            output += sl + linebreak
        # Add the rest
        if len(block) > 2:
            for line in block[2:]:
                output += line.rstrip() + linebreak

        return output

    output = []

    # split into blocks
    lines = page.split("\n")
    blocks = []
    cblock = []
    for line in lines:
        if line.strip() == "":
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
            output.append("")
            continue
        # obsidian callout
        if re.match(r"^\s*>\s*\[!.*?\]", block[0]):
            output.append(convert_block(block))
            continue
        # normal block
        output += block + [""]

    return "\n".join(output)
