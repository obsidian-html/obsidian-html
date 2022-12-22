> This page is outdated!

# Architecture
## High level
The conversion from Obsidian Notes to an HTML site goes in three steps:
- Obsidian Notes are converted to proper markdown
- Markdown notes are converted to html pages
- Extra files are added to the html output to make a functioning site possible

It is possible to only convert obsidian notes to proper markdown (`toggles/compile_html = False`), or to only convert proper markdown to a html site (`toggles/compile_md = False`). 

## Obsidian notes to proper markdown
Most of the relevant conversions will be done in this step. At the end of this step, a folder of proper markdown is generated that is guaranteed to be fully functional in at least Github markdown viewer.

An entrypoint is given, which is a path to a note file, that is inputted into `crawl_obsidian_notes_and_convert_to_markdown()`. This function will handle the conversion to a proper markdown file, and call itself on any markdown files that are linked in the entrypoint note. This process continues recursively, until the entire tree has been processed.

Note that this means that not all the notes will be converted, only the notes that are reachable from the entrypoint note, in however many steps.

The converted proper markdown notes will be written with preserved relative path to the folder `md_folder_path_str` in the config file. The entrypoint path will be rewritten to `md_folder_path_str + '/index.md'` and serve as the entrypoint for the next step.

## Proper markdown to Html
This is done by `crawl_markdown_notes_and_convert_to_html()`. Just like `crawl_obsidian_notes_and_convert_to_markdown()`, this function will take an entrypoint file, and follow markdown links to recurse through the files.

The most important tranformation in this process is to rewrite the links so that they all become an absolute path. When `html_url_prefix` is set in the config yaml, this will be added as a prefix to every link. This allows one to deploy to a target of `<host>/folder/` instead of `<host>/`. 

Just like in the previous step, image files and the like get copied over to the output directory.

Other transformations are made to enable html features that mimic the function of Obsidian, such as color coding external links, and links to non-existent links.

Links that point to notes that have not been created will be rerouted to the `not_created.html` page. 

After the markdown notes are converted to html through the use of `python-markdown`, they are merged with the html code from `src/template.html`. Every page is identical, as in, every page is just the template.html with the note inserted in it body section.

## Extra files are added to the html output to make a functioning site possible
Files like `main.css`, fonts, etc, are copied over to the output folder.

# Javascript code
All the javascript code that enables the tabbing behavior seen in the final website that is generated is located in `template.html`. When tabbing and other such features are not desired, this javascript can be stripped from the template. 

The most notable effect this will have is that the links are not rewritten, and thus will just open every link as a new page.

# Code standards
## Paths
This code handles with a lot of path arithmatic. This is done via the Pathlib.Path library. The following convention applies:
- Variables that contain a Path object are named `*_path`
- *Input* variables that contain any kind of path in the form of a string, are named `*_path_str`
- When loading Path objects from strings, the method `.resolve()` is always called on it to get a full path
- Relative paths are named `rel_*`