# Developer documentation
## Install custom code
These steps describe how to install the requirements and use obsidianhtml from the code, instead of installing it as a package. This way you can quickly test changes.

``` bash
# Get the code
# Note that the master branch is work in progress! Code might be broken. 
# Move into a release branch if you want fully tested code instead.
git clone git@github.com:obsidian-html/obsidian-html.git

# Move into folder
cd obsidian-html

# Install all the dependencies of the package, but not the package itself.
# You only need to do this once.
pip install .

# Run ObsidianHtml from code (so not via the package)
python -m obsidianhtml -i /path/to/config.yml
```

## Contribute to Obsidianhtml
## Introduction
When contributing code to the project, please take into consideration the following requirements:
- Run a linter to avoid obvious errors
- Run black to apply standardizes formatting, so that we don't pollute PR's with format changes

### Running linting
To avoid easily avoidable errors, it is good to run a linter before commiting your code to be pulled.

I know of two linters as of writing this, pylint and ruff.

Ruff is supposed to be a lot faster than pylint. The two sections below will explain how to run each.
You can choose either.

### Run pylint

For first time setup, run the following:
``` shell
pip install pylint
```

Then, when ready to commit, run the following in the root of this repo:
``` shell
pylint obsidianhtml --errors-only --disable=E0602,E1126
```

Resolve any issues. 

After a proper refactor we can remove some of these options to give more suggestions, but the command above is the main goal.

The disabled codes of E0602,E1126 are done because pylint is buggy / not knowledgable enough and creates false errors. Once in a while we can remove these codes and see if there are
new errors that *can* be solved, but as of writing the only errors it spits out with these codes are false ones.

For refactoring, this is the current shortlist:

``` shell
pylint obsidianhtml --disable=E0602,E1126,R0401,R0801,R1702,C0201,C0301

# R1702: too many nested blocks. Would use fewer if I could!
# R0801: duplicate code. Not always an issue. Don't want to have to worry about a thousand dependants when changing a module.
# R0401: cyclic import. Does not find cyclic imports, seems to find very long import chains.
# C0201: Consider iterating the dictionary directly instead of calling .keys()
#        I like the clarity of iterating over keys, to visually remind me that we are not looping over the values.
# C0301: Line too long. Deal with it. Comments can make the line longer, I don't want to break the flow with extra comment lines.
```

Find trailing whitespace in a file with vscode:
``` 
Press ctr+f
Select the .* icon
Search for: [^\s]+ +\n
```

### Run Ruff
For first time setup, run the following:
``` shell
pip install ruff
```

See pyproject.toml for configuration

Then, when ready to commit, run the following in the root of this repo:
``` shell
ruff check obsidianhtml  
```

### Run black
For first time setup, run the following:
``` shell
pip install black
```

See pyproject.toml for configuration

Then, when ready to commit, run the following in the root of this repo:
``` shell
black obsidianhtml
```

# Architecture
[Architecture & Code standards](architecture.md)
