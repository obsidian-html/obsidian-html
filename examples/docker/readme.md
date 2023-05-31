# Run obsidianhtml in a Docker container

## Introduction
This page aims to explain how to use docker to run obsidianhtml.
This might help setting up obsidianhtml on a system that has issues running obsidianhtml natively.

## Prerequisites
Make sure to install Docker before following the instructions below

- https://docs.docker.com/get-docker/


### On Windows
For Windows, you can choose Docker Desktop for Windows.

After the installation is done, open Docker Desktop, and accept the agreement, this will start the Docker daemon.

After that is done, open a **new** Powershell window. (Not Powershell ISE!)

Run `docker` in Powershell to test that the application is registered and working.

## Instructions
``` bash
cd ~
mkdir git
cd git

# if you are behind a proxy, first set:
# git config --global http.proxy http://proxyUsername:proxyPassword@proxy.server.com:port

# clone this project and move into it
git clone https://github.com/obsidian-html/obsidian-html.git
cd obsidian-html

# build the image
docker build . -t local/obsidianhtml

# go into this folder
cd examples/docker

# open ./config/config.yml and configure it
# set at least obsidian_entrypoint_path_str
# (On Windows, use an application other than vim)
vim ./config/config.yml

# set config
VAULT_PATH="/home/dorus/git/example_vault/vault"
OUTPUT_PATH="/tmp/output"

# make sure output folder exists on our system
# (On Windows, -p will be ignored, you will get an error if the folder already exists, this is fine)
mkdir -p $OUTPUT_PATH

# run container
docker run \
    --mount type=bind,source="$(pwd)/config",target=/config \
    --mount type=bind,source="$OUTPUT_PATH",target=/output \
    --mount type=bind,source="$VAULT_PATH",target=/input \
    local/obsidianhtml
```

That should give you output that ends in:
```
(...)
< COMPILING HTML FROM MARKDOWN CODE: Done

You can find your output at:
        md: /output/md
        html: /output/html
```

Note that the reported output paths are within the context of the container, you should look instead under the folder 
configured in `$OUTPUT_PATH` for your files.

## Troubleshooting

If you need to troubleshoot, and want to look inside of the containers at the folders `/input`, `/config`, and `/output`, run this command to enter the container:

``` bash
docker run \
    --mount type=bind,source="$(pwd)/config",target=/config \
    --mount type=bind,source="$OUTPUT_PATH",target=/output \
    --mount type=bind,source="$VAULT_PATH",target=/input \
    --rm -it --entrypoint bash \
    local/obsidianhtml
```

## Run a different command
If you want to get the version, for example, you can run the following (equivalent to `obsidianhtml version`)

``` bash
docker run \
    --rm -it --entrypoint "obsidianhtml" \
    local/obsidianhtml \
    version
```