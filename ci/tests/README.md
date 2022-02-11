# Regression testing

> This page is under construction

## Installation

```sh
pip install requests
pip install beautifulsoup4
pip install html5lib
python ci/tests/basic_regression_test.py
```

## Run tests via docker

```sh
docker build -t obsidian-html-test .; docker image rm obsidian-html-test
```
