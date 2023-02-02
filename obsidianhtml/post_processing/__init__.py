
def convert_markdown_output(pb, convert_function, arg_dict=None):
    for file in pb.paths['md_folder'].rglob("*.md"):
        with open(file, 'r') as f:
            content = f.read()
        content = convert_function(content, **arg_dict)
        with open(file, 'w') as f:
            content = f.write(content)