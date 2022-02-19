FROM python:3.10 as base
COPY . /obsidian-html
RUN cd /obsidian-html && pip install --upgrade pip && pip install . && pip install lxml
RUN cd /obsidian-html && python ci/tests/basic_regression_test.py
