FROM python:3.10 as base
#RUN apt update
#RUN apt install -y firefox-esr
#RUN pip install --upgrade pip && pip install lxml selenium markdown obsidianhtml-md-mermaid-fork python-frontmatter pygments regex requests beautifulsoup4 html5lib
RUN pip install --upgrade pip && pip install lxml markdown obsidianhtml-md-mermaid-fork python-frontmatter pygments regex requests beautifulsoup4 html5lib
COPY . /obsidian-html
RUN pip install obsidian-html/ --upgrade 
RUN python obsidian-html/ci/tests/basic_regression_test.py
#RUN cd /obsidian-html && python ci/tests/selenium_tests.py   
