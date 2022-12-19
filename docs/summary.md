
- MarkdownPage.ConvertObsidianPageToMarkdownPage()
  - [1] Replace code blocks with placeholders so they aren't altered & [1] Restore codeblocks/-lines
    - MarkdownPage.ConvertObsidianPageToMarkdownPage() --> MarkdownPage.StripCodeSections() & MarkdownPage.RestoreCodeSections()
  - [2] Add newline between paragraph and lists
  - [3] Convert Obsidian type img links to proper md image links
  - [4] Handle local image links (copy them over to output)
  - [5] Change file name in proper markdown links to path
  - [6] Replace Obsidian links with proper markdown
  - [7] Fix newline issue by adding three spaces before any newline
  - [8] Insert markdown links for bare http(s) links (those without the `[name](link)` format).
  - [9] Remove inline tags, like #ThisIsATag
  - [10] Add code inclusions
- crawl_markdown_notes_and_convert_to_html()
  - [4] Handle local image links (copy them over to output) 
  - [11] Convert markdown to html
    - [11.1] Rewrite .md links to .html (when the link is to a file in our root folder)
    - [11.2] Adjust image link in page to new dst folder (when the link is to a file in our root folder)
  - [12] Copy non md files over wholesale, then we're done for that kind of file
  - [13] Link to a custom 404 page when linked to a not-created note
  - [14] Tag external links with a class so it can be decorated differently
  - [15] Tag not created links with a class so it can be decorated differently
  - [16] Wrap body html in valid html structure from template
  - [17] Show a graph view per note
  - [18] Display backlinks to note


[425] Add included notes to graph view as a link
  When including code from another note, during n->m, add the link to the included note to the metadata of the current note, at obs.html.data/inclusion_references
  During m->h, read out obs.html.data/inclusion_references and add each link to the networktree using link_type="inclusion"