An application to export Obsidian notes to standard markdown and an html based website.

See the github repository for the code, to raise issues, and further information: https://github.com/obsidian-html/obsidian-html

You can see the capabilities of this system in this demo website: https://obsidian-html.github.io/. 

**Note**: this code is actively worked on. There is comprehensive testing, but there is no test regiment before pushing. Things may break because of the frequent changes! Let me know if something does not work as expected or advertised.

**What it does**:
The Obsidian notes will be converted to standard markdown output. Then, optionally, html output is created based on the standard markdown. 
It is also possible to input existing standard markdown to just use the markdown to html functionality.

To convert your notes, you need to point to your notes folder, and to one note that will serve as the index.html page.

Only notes that are found by following links recursively, starting with the entrypoint, will be converted! 

**Changelog**:

- 0.0.7: Added mermaid support   
- 0.0.6: Bugfix for Linux paths   
- 0.0.5: Tag list added.   
- 0.0.4: Added the option to use a custom html template, and to export the packaged template.   
- 0.0.3: Updated readme file to work with pypi.   
- 0.0.2: Updated readme file to work with pypi.   