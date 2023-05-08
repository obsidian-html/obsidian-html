from functools import cache


@cache
def gc_add_toc_when_missing(pb, fo):
    if "obs.html.tags" in fo.md.metadata.keys() and "dont_add_toc" in fo.md.metadata["obs.html.tags"]:
        return False
    depr = pb.gc("toggles/features/styling/add_toc")
    if depr != "<DEPRECATED>":
        return depr
    return pb.gc("toggles/features/table_of_contents/add_toc_when_missing")


def add_toc_when_missing(pb, page, md_metadata):
    if "[TOC]" in page:
        return page

    # compile output where TOC is placed under the first h1
    output = ""
    found_h1 = False
    for line in page.split("\n"):
        output += line + "\n"
        if found_h1 is False and line.startswith("# "):
            output += "\n[TOC]\n\n"
            found_h1 = True

    # If h1 is at the top of the note, this will overwrite the embedded title.
    # In this case, we always need to put the TOC under the first h1
    h1_at_top_of_note = False
    for line in page.split("\n"):
        if line.strip() == "":
            continue
        if line.startswith("# "):
            h1_at_top_of_note = True
            break
        break

    if h1_at_top_of_note:
        return output
    else:
        # test if embedded titles are disabled
        et_cap_enabled = pb.capabilities_needed["embedded_note_titles"]
        et_disabled_in_note = "obs.html.tags" in md_metadata.keys() and "dont_add_embedded_title" in md_metadata["obs.html.tags"]
        embedded_titles_disabled = et_cap_enabled and not et_disabled_in_note

        # If there is an h1 on the pace, and we are not using embedded titles, put the TOC under the first h1
        # Otherwise just put it at the top of the page.
        if found_h1 and embedded_titles_disabled:
            return output
        else:
            return "\n[TOC]\n\n" + page
