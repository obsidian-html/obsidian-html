**Important note**:    
Only recently I learned that there used to be a similar package under the same name. That one seems to have been renamed to Oboe. The original was located at https://github.com/kmaasrud/obsidian-html and later https://github.com/kmaasrud/oboe which you find referenced in a lot of places. I would link to it but I can't find an authoritative source, only forks. Anyways: **This is not that package**. 


# Obsidian-html
An application to export Obsidian notes to standard markdown and an html based website.

> You can see the capabilities of this system in this demo website: [Example of the HTML output](https://obsidian-html.github.io/). This site also functions as a nice documentation for all things not mentioned on this page.

## Examples of actual sites using this system
- [Devfruits.com/Notes](https://devfruits.com)

> **Note**: this code is actively worked on. There is comprehensive testing, but there is no test regiment before pushing. Things may break because of the frequent changes! Let me know if something does not work as expected or advertised.

## What does it do?
The Obsidian notes will be converted to standard markdown output. Then, optionally, html output is created based on the standard markdown. 
It is also possible to input existing standard markdown to just use the markdown to html functionality.

To convert your notes, you need to point to your notes folder, and to one note that will serve as the index.html page.
Only notes that are found by following links recursively starting with the entrypoint will be converted. 

> If you wish to convert all the notes, please create an issue requesting this feature.

# Developer documentation
For developers: [Developer Documentation](docs/developer_docs.md)

# Installation
- First install python 3 (>= 3.9)
- Open your terminal of choice
- (Optional) Create and enter a virtual environment

Then run:
  ``` bash
  # For the latest published version
  pip install obsidianhtml

  # For the latest version in this repository
  pip install git+https://github.com/obsidian-html/obsidian-html
  ```

To uninstall, run:
``` bash
pip uninstall obsidianhtml
```

# Useage
> This application is extensively tested on Windows, and currently used by the main developer on Linux.

- Download the [example_config.yml](example_config.yml) file to your local system, and rename it to `config.yml`.
- Open config.yml and edit the settings, see the comments there. At the very least, edit the following variables:

| Variable | Description |
| :------- | :---------- |
| `obsidian_folder_path_str` | Find the root folder of your obsidian notes. This is the first folder that contains any markdown files or multiple folders with markdown files. Set this variable to its full path |
| `obsidian_entrypoint_path_str` | Set to the full path of the note that will serve as your index.html. This should be in the root above, but may be in a subdirectory. |
| `md_folder_path_str` | Set to some folder where you want to write the markdown files to |
| `md_entrypoint_path_str` | This has to be md_folder_path_str + '/index.md' when toggles/compile_md == True. Otherwise, set as full path of the markdown file that will serve as your index.html.  |
| `html_output_folder_path_str` | Set to some folder where you want to write the html files to |

- Then, open your terminal of choice (and enter your virtual environment if you installed obsidianhtml in one).
- Run 
  ``` bash
  obsidianhtml -i /path/to/your/config.yml
  ```

Optionally append command-line toggles, such as:
- `-v` verbose output in console

To view the html as a website, do the following:
- Open a terminal
- Run `python -m http.server --dir /path/to/your/html/output/folder`
- Open [http://localhost:8000](http://localhost:8000)

## Use a custom html template
By default, obsidianhtml will use its packaged html template to compile the html output.
To change this, first export the packaged template to a given path:

``` bash
obsidianhtml -eht C:\Users\User\Downloads\template.html
```

Then, open and edit your exported template. Note that the string '{content}' should remain present somewhere in the template.
Finally, pass the path to your custom template as an input variable. Open your config.yml, and fill in the full path under `html_template_path_str`.

This will make sure future runs of obsidianhtml will use your custom template (provided that you use that specific yaml file as input).

# Features
## Not supported
- Inline tags (you can use them in Obsidian, but they are ignored in the conversion). Frontmatter tags are converted to a tag list, see below.
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

There is also a newline added between non-list lines and list lines. This to copy Obsidian's allowance to create a list without needing to put a newline in front of it.

## Obsidian code inclusions
When using the format `![[Name of note]]`, the contents of the note will be included. In Obsidian, the inclusion is denoted by wrapping a div around the content. This is not possible in the intermediate markdown code, so all inclusions are just pasted in as-is. 

This package also supports partial inclusions. You can use this by writing `![[Name of note#Chapter Name]]`. In this case, only that chapter and its contents until the next chapter of the same depth is included. See also [Example Website#partial-code-inclusion](https://obsidian-html.github.io/#!partial-code-inclusion).

## Frontmatter Tag list
Inline tags are excluded, but those listed in the yaml frontmatter are compiled into a list.
When running your website, go to `/tags` to view the tag list. [Example](https://obsidian-html.github.io/tags/).

## Basic Templating
All generated html code will be wrapped by the html code in `src/template.html`. This template points to `src/main.css`. 
Change this code *in the `/src` folder* to have the changes persist across runs of the code (output will be overwritten).

Links that point to non-existent notes will be redirected to `output/html/not_created.html`, the base code for this is located at `/src/not_created.html`.

## Other features
- Syntax highlighting built-in
- [Very clean html + minor javascript website output](https://www.devfruits.com)
- Mermaid diagrams supported using md-mermaid
- See the [Example Website](https://obsidian-html.github.io/) for the most up to date list of supported features!


# Quirks
## Toggle: relative_path_md
This toggle controlls whether links to/out of folders are done in a relative or an absolute way. 

Github seems to work best with relative links (I had trouble with / prefixed paths as full paths). 
Whereas a Gitlab project I've tested this on seemed to exclusively use full-path links.

Let's say we have the following files, all linking to eachother:
```
/folder1/page1.md
/folder1/page2.md
home.md
```

With relative_path_md to True, we'll get these links in the md:
```
folder1/page1 --> folder1/page2: page2.md
folder1/page1 --> home: /home.md
home --> folder1/page1: folder1/page1.md
```

Or, with how the code works atm (comes down to the same principle):

```
folder1/page1 --> folder1/page2: ../folder1/page2.md
folder1/page1 --> home: ../home.md
home --> folder1/page1: folder1/page1.md
```

With it on False, we'll get
```
folder1/page1 --> folder1/page2: /folder1/page2.md
folder1/page1 --> home: /home.md
home --> folder1/page1: /folder1/page1.md
```

I'd recommend just running the code, and if you are missing files that live in folders, toggle the switch to the other value and try again to see if that fixes it.

The html code just used full paths everywhere because this gives me headache and is more foolproof.
