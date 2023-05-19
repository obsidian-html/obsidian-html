FROM python:3.9.14 as base
#RUN apt update
#RUN apt install -y firefox-esr
#RUN pip install --upgrade pip && pip install lxml selenium markdown obsidianhtml-md-mermaid-fork python-frontmatter pygments regex requests beautifulsoup4 html5lib

RUN apt update
RUN apt install -y rsync
ENV VIRTUAL_ENV=/opt/venv
ENV OBS_HTML_USE_PIP_INSTALL true
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
#RUN pip install --upgrade pip && pip install lxml markdown obsidianhtml-md-mermaid-fork python-frontmatter pygments regex requests beautifulsoup4 html5lib
COPY . /obsidian-html
WORKDIR /obsidian-html
RUN pip install --upgrade pip && pip install .
RUN python ci/tests/basic_regression_test.py
#RUN cd /obsidian-html && python ci/tests/selenium_tests.py   
