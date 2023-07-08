import json
import re


class SearchHead:
    def __init__(self):
        self.data = []

    def AddPage(self, url, rtr_url, filename, title, content, metadata):
        p = {
            "file": filename,
            "path": rtr_url,
            "title": title,
            "url": url,
            "rtr_url": rtr_url,
            #'keywords': GetKeywords(content),
            "content": SanatizeText(content),
            "tags": GetTags(metadata),
        }
        self.data.append(p)

    def AddFile(self, gc, fo):
        """Used to be able to find files as well as notes"""
        if not (gc("toggles/features/search/enabled", cached=True) and gc("toggles/features/search/add_files", cached=True)):
            return

        rtr_url = fo.path["html"]["file_relative_path"].as_posix()
        url = fo.get_link("html")
        filename = fo.path["html"]["file_relative_path"].name
        p = {
            "file": filename,
            "path": rtr_url,
            "title": filename,
            "url": url,
            "rtr_url": rtr_url,
            "content": filename,
            "tags": filename,
        }
        if p not in self.data:
            self.data.append(p)

    def OutputJson(self):
        """the search.json"""
        # return json.dumps(self.data, ensure_ascii=False).encode('utf8')
        return json.dumps(self.data)


def SanatizeText(text):
    text = text.lower()
    text = text.replace("\n", " ↩ ")
    text = re.sub(r"[\s]{2,}", " ", text)
    text = re.sub(r"[\s↩]{2,}", " ↩ ", text)

    return text


def GetKeywords(text):
    # clean up text
    text = text.lower()
    text = text.replace("%20", " ")
    text = text.replace("---", " ")
    text = "".join([(" " if ch in '="[]{}()<>/.,:\\\n\t`_^$&#*' else ch) for ch in text])

    # get rid of starting/ending quotes
    words = []
    t_words = text.split(" ")
    for word in t_words:
        if len(word) == 0:
            continue

        if word[0] == "'" or word[0] == '"':
            word = word[1:]

        if len(word) == 0:
            continue

        if word[-1] == "'" or word[-1] == '"':
            word = word[:-1]

        if len(word) == 0:
            continue

        words.append(word)

    # get set of unique words
    s_words = " ".join(list(set(words)))

    return s_words


def GetTags(metadata):
    if "tags" in metadata.keys():
        return " ".join(metadata["tags"])
    return ""
