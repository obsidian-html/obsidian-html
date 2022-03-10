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
docker build -t obsidian-html-test .; docker image rm obsidian-html-test
```
