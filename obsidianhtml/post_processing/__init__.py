from pathlib import Path

def convert_markdown_output(md_folder_path, convert_function, arg_dict=None):
    for file in Path(md_folder_path).rglob("*.md"):
        with open(file, 'r') as f:
            content = f.read()
        content = convert_function(content, **arg_dict)
        with open(file, 'w') as f:
            content = f.write(content)