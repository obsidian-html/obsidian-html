# Obsidian-html [![TestSuite](https://github.com/obsidian-html/obsidian-html/actions/workflows/test.yml/badge.svg)](https://github.com/obsidian-html/obsidian-html/actions/workflows/test.yml)

**Important note**:
Only recently I learned that there used to be a similar package under the same name. That one seems to have been renamed to Oboe. The original was located at https://github.com/kmaasrud/obsidian-html and later https://github.com/kmaasrud/oboe which you find referenced in a lot of places. I would link to it but I can't find an authoritative source, only forks. Anyways: **This is not that package**.

## Description

An application to export Obsidian notes to standard markdown and an html based website.

You can see the capabilities of this system in this demo website: 
- [Example of the HTML output](https://obsidian-html.github.io/). 

This site also functions as a nice documentation for all things not mentioned on this page.

## Alternatives
This solution might not be the best for your usecase. Check out the [alternatives section](#alternatives-1) to compare other solutions to this one.

## What does it do?
The Obsidian notes will be converted to standard markdown output. Then, optionally, html output is created based on the standard markdown. 
It is also possible to input existing standard markdown to just use the markdown to html functionality.

To convert your notes, you need to point to your notes folder, and to one note that will serve as the index.html page.

By default only notes that are found by following links recursively starting with the entrypoint will be converted. To include all notes in your folder, see the [process_all setting](https://github.com/obsidian-html/obsidian-html/blob/f0cccc3bf7f2dd0deaf5654d2de46d7b5aa51c35/obsidianhtml/src/defaults_config.yml#L78-L80).

## Compatibility
 - This application is extensively tested on Linux/OSX, and occasionally tested on Windows.
 - Python version 3.9 or higher is required
 - Make sure that the `python` command points to `python3`, and not a python2 version.

# Developer documentation
For developers: [Developer Documentation](docs/developer_docs.md)

# Installation
- First install python 3 (>= 3.9)
- Often you need to update pip after installing python to have it work.
  ```
  pip install --upgrade pip
  ```
- Open your terminal of choice
- (Optional) Create and enter a virtual environment

Then run:
  ``` bash
  # For the latest published version
  pip install obsidianhtml

  # For the latest version in this repository
  # (Note that the master branch is work in progress, so we take a release branch)
  pip install git+https://github.com/obsidian-html/obsidian-html@releases/0.0.9
  ```

To uninstall, run:
``` bash
pip uninstall obsidianhtml
```

# Useage
- Download the [defaults_config.yml](obsidianhtml/src/example_config.yml) file to your local system.
  - Alternatively run (on Linux/OSX)
    ``` bash
    obsidianhtml -gc > config.yml
    ``` 
- This file is used by the package to fill in all the defaults. The input that you are required to fill in is clearly marked. Open the file and change these values. 
- The rest of the settings can be removed from your copy of the file. 

Below is some information on the required input and other input that you might want to change for the first run:

| Variable | Description |
| :------- | :---------- |
| `obsidian_folder_path_str` | Find the root folder of your obsidian notes. This is the first folder that contains any markdown files or multiple folders with markdown files. Set this variable to its full path |
| `obsidian_entrypoint_path_str` | Set to the full path of the note that will serve as your index.html. This should be in the root above, but may be in a subdirectory. |
| `md_folder_path_str` | Set to some folder where you want to write the markdown files to. |
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

# Configuration options
> See the [Example Website](https://obsidian-html.github.io/) for a more extensive / more up to date list of supported features/options!

## Modes
These are settings that have a big impact on the way ObsidianHtml works.
### Process_all
If **false**, ObsidianHtml will take your entrypoint note, convert it, and then continue to any note that is linked to by the entrypoint note. This continues until all linked notes are converted.

If **true**, all<sup>*</sup> notes in the entrypoint folder will be converted, irregardless if they are linked to

> <sup>*</sup> You can exclude folders from being processed at all using the [exclude_subfolders](https://github.com/obsidian-html/obsidian-html/blob/f0cccc3bf7f2dd0deaf5654d2de46d7b5aa51c35/obsidianhtml/src/defaults_config.yml#L34-L40) setting.


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
## Not supported on purpose
- Inline tags (you can use them in Obsidian, but they are ignored in the conversion). Frontmatter tags are converted to a tag list, see below. 

> If you miss a feature in Obsidian that is not handled by ObsidianHtml, or if you have a real usecase for features in this list, that are intentionally not supported (yet), please create an issue and let us know.


## Basic Templating
All generated html code will be wrapped by the html code in `src/template.html`. This template points to `src/main.css`. 
Change this code *in the `/src` folder* to have the changes persist across runs of the code (output will be overwritten).

Links that point to non-existent notes will be redirected to `output/html/not_created.html`, the base code for this is located at `/src/not_created.html`.


See the [Example Website](https://obsidian-html.github.io/) for a more extensive / more up to date list of supported features!


# Quirks
## Be careful with these folder names in your vault
The following folders will be created in the HTML output, that might overwrite any notes that you have in similarly named folders:

- `tags`
- `98682199-5ac9-448c-afc8-23ab7359a91b-static` (okay, this one is prefixed with a guid exactly because we want to avoid overwriting your notes in the output.)

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

# Alternatives
This package might not be what you are looking for. I will keep a list here of other options that I find online for publishing Obsidian notes to webpages.

The **extra features** will list features that these solutions have that are not found in many other solutions.

## Perlite
`have not tried this myself yet`
- Source: https://github.com/secure-77/Perlite
- Example site: https://perlite.secure77.de/
- Technology: php
- Extra features:
  - Search
  - Fullscreen mode
- Good things:
  - Very clean website design
  - Nice vertical navigation menu
- Bad things:
  - I haven't run this solution yet. None that I can find from documentation

## Pubsidian
`have not tried this myself yet`
- Source: https://github.com/yoursamlan/pubsidian
- Example site: https://yoursamlan.github.io/pubsidian/
- Technology: python
- Extra features:
  - Graph view
  - Toggle light/dark mode
- Good things:
  - Responsive website design
  - Has a [Windows installer](https://github.com/yoursamlan/pubsidian#pubsidian-convert-gui-v10) to help you convert your Obsidian notes to a website
- Bad things:
  - I haven't run this solution yet. None that I can find from documentation. Seems to miss tag-related features.


## Gatsby Garden
`have not tried this myself yet`
- Source: https://github.com/binnyva/gatsby-garden/
- Example site: https://notes.binnyva.com/
- Technology: node, npm
- Extra features:
  - Graph view
  - Sitemap, RSS Feed
- Good things:
  - Very clean website design
- Bad things:
  - Notes should be in a specific location to work (= copypasting when you have multiple vaults)
 
## ObsidianToHtmlConverter
- Source: https://github.com/klalle/ObsidianToHtmlConverter
- Example site: n/a
- Technology: python script
- Extra features:
  - None
- Good things:
  - Very simple
- Bad things:
  - Very simple (lacks many features)
  - Bad looking default html output (personal opinion)
  - Uses a homebrew solution for converting markdown to html 
