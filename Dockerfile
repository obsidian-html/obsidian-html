FROM python:3.10 as base
COPY . /obsidian-html
RUN cd /obsidian-html && pip install . && pip install requests && pip install beautifulsoup4 && pip install html5lib
RUN cd /obsidian-html && python ci/tests/basic_regression_test.py
