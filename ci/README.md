# Regression testing

## Documentation
I've written a couple of Jupyter notebooks to go through some test setups.

This is most useful for Selenium, as starting it up takes a non trivial amount of time, and
Jupyter allows us to keep selenium open while we add extra tests.

### Install jupyter
On linux:
``` bash
pip install jupyter
cd path/to/this/repo/ci/docs
jupyter notebook
```

Then open one of the notebooks


## Run tests via docker

```sh
docker build -t obsidian-html-test -f CIDockerfile .; docker image rm obsidian-html-test
```


# Unit testing
## First time setup
Make sure to install the following packages that are not installed by default when installing obsidianhtml, 
because they are only used for testing:
``` shell
pip install termcolor
```

## Run
Move to the root of this repo, and then:
``` shell
python ci/tests/unit_test_obs_img_to_md.py
``` 