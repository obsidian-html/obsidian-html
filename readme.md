# Obsidian-html
An application to export Obsidian notes to standard markdown and an html based website.

You can see the capabilities of this system in this demo website: [Example of the HTML output](https://obsidian-html.github.io/). 

## Setup
The Obsidian notes will be converted to standard markdown output. Then, optionally, html output is created based on the standard markdown. 
It is also possible to input existing standard markdown to just use the markdown to html functionality.

To convert your notes, you need to point to your notes folder, and to one note that will serve as the index.html page.
Only notes that are found by following links recursively starting with the entrypoint will be converted. If you wish to convert all the notes, please create an issue requesting this feature.

> Note, this code has not been fully tested yet. Work in progress. Issues and/or pull requests are welcomed!


## Examples of actual sites using this system
- [Devfruits.com/Notes](https://devfruits.com)

# Installation
First install python 3, then:

``` bash
python -m pip install --upgrade pip
pip install markdown python-frontmatter pygments
```

# Useage
This application is only tested on Windows, though it should be relatively easy to get working for Linux.

- Git clone this repository
- Find the root folder of your obsidian notes. This is the first folder that contains any markdown files or multiple folders with markdown files.
- Open powershell and navigate into the cloned folder
- Run `python run.py 'C:\Users\Installer\OneDrive\Obsidian\Notes' 'C:\Users\Installer\OneDrive\Obsidian\Notes\Work.md'`, where the first filepath should be changed to point to your root folder, and the second filepath should point to the file that you want to serve as the index.html

> **Note**: Only notes that are found by following links recursively starting with the entrypoint will be converted. If you wish to convert all the notes, please create an issue requesting this feature.

The script then writes converted (standard format) markdown files to `output/md`, and html files to `output/html`.

To test the html files, run `python -m http.server --directory output/html` then open [http://localhost:8000]()

# Features
## Not supported
- Tags (you can use them in Obsidian, but they are ignored in the conversion)
- Possibly a lot more

## Conversion of Obsidian type links
- `[[Page Link]]` is converted to the standard `[Page Link](correct_path_to_file.html)` link format
- `[[Page Link|Alias]]` is converted to `[Alias](correct_path_to_file.html)`
- When the determined path is the same as the entrypoint note, the link will be `[Page Link](/)` (i.e. the index.html)

Here, it doesn't matter if the target file is in another folder, as long as all the notes are in the root folder somewhere.

## Conversion of Obsidian type image links
- `![[image.png]]` is converted to the standard `![](rel/path/to/image.png)`

Confusingly, code inclusions use the same format, but point to .md files. There is a simple test if the string ends in a common image suffix and if not the Obsidian code inclusion is handled (not supported yet), otherwise the link is converted to a standard image link.

## Conversion of Obsidian 'bare links'
If you type `http(s)://....` in Obsidian, it will automatically convert it to a link. Any string that:
- Starts with "http"
- Ends with a space or newline
- Is **not** preceeded by an '[' or '('

will be converted to `[matched value](matched value)`

## Conversion of Obsidian newline behavior
Three spaces are added behind every newline to simulate Obsidian's "enter = new line" behavior. Note that not all markdown readers comply with this standard, but python-markdown does, so the outputted HTML is as expected.

## Basic Templating
All generated html code will be wrapped by the html code in `src/template.html`. This template points to `src/main.css`. 
Change this code *in the `/src` folder* to have the changes persist across runs of the code (output will be overwritten).

Links that point to non-existent notes will be redirected to `output/html/not_created.html`, the base code for this is located at `/src/not_created.html`.

## Other (expected) features
- Syntax highlighting built-in
- [Very clean html + minor javascript website output](https://www.devfruits.com)

# Future developments
- This code would make a good python-markdown extension, might build that in the future.
