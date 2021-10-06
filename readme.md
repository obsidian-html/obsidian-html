# Obsidian-html
An application to export Obsidian notes to an html based website

# Installation
First install python 3, then:

``` bash
python -m pip install --upgrade pip
pip install markdown
pip install python-frontmatter
```

# Useage
This application is only tested on Windows, though it should be relatively easy to get working for Linux.

- Git clone this repository
- Find the root folder of your obsidian noted. This is the first folder that contains all of your markdown files
- Open powershell and navigate into the cloned folder
- Run `python run.py 'C:\Users\Installer\OneDrive\Obsidian\Notes' 'C:\Users\Installer\OneDrive\Obsidian\Notes\Work.md'`, where the first filepath should be changed to point to your root folder, and the second filepath should point to the file that you want to server as the index.html

The script then writes converted (standard) markdown files to `output/md`, and the html files to `output/html`.

To test the html files, run `python -m http.server --directory output/html` then open [http://localhost:8000]()