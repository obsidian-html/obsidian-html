

# Objects
The main code is organised like this:

- Config: Takes user input to load a config yaml into a list of settings
- Index: Reads the input folder and processes it into a list of Nodes
- Node: Represents a "page", be it the original obsidian note, a markdown note, or the html page.
- Picknickbasket: An object that can be passed into most functions in lieu of global variables. Contains other objects such as Config and NetworkTree
- NetworkTree: Keeps track of the relationship between nodes. Used for create_index_from_tags, graph view, etc.

## ConfigManager/Config
The config object takes all the user configuration and:

- Merges the default config and the user config
- Tests the config for illegal configurations
- Fills in missing values (e.g. finding the obsidian vault based on the entrypoint note)

## Index
The index is an object that aims to load all the input files and process them into Node objects so that we can work with them.
THe index object is responsible for:

- Finding all the files within the given vault/markdown folder
- Filtering out excluded folders / files
- Generating the file tree object

## v4/Node/Node
A node is an object that can represent any of the following:

- An obsidian note
- A markdown page
- An html page
- A "dot" in the graph view

The node object has been added to manage the state change from note --> markdown, and markdown --> html.

The node object uses the following objects from the older versions of obsidianhtml:

- fo <FileObject> "file object"
- md <MarkdownPage 


### Life cycle
``` python
# instantiate new node
node = Node(pb)

# init node from obsidian note
node.from_obsidian('/rtr/path/to/obsidian/note.md')

# init node from markdown pagn
node.from_markdown('/rtr/path/to/obsidian/note.md')

```

# Flow
## Config input by users
```
ConvertVault/ConvertVault
    pb.loadConfig(config_yaml_location)
        config_yml <- ConfigManager/find_user_config_yaml_path
                        - read function input for value, if empty:
                        - read sys args for input, if empty:
                        - read current folder for config.yml, if nonexistent:
                        - read current folder for config.yaml, if nonexistent:
                        - read default appdir location for config.yml
        config_yml -> ConfigManager/Config
```

## Reading the file tree
```
ConvertVault/ConvertVault
    ft = FileTree(pb)     # compiles excluded folders list, sets root
    ft.load_file_tree()   # find all files, convert them into fo's, add them to dict, keyed to rtr file path  