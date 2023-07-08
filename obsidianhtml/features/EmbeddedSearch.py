import os
import sys
import json
import gzip
import shutil

from pathlib import Path

from whoosh import index
from whoosh.qparser import MultifieldParser, OrGroup
from whoosh import fields

from ..lib import print_global_help_and_exit, get_obshtml_appdir_folder_path


def InitWhoosh(index_dir):
    schema = fields.Schema(
        id=fields.ID(stored=True),
        path=fields.TEXT(stored=True),
        file=fields.TEXT(stored=True),
        title=fields.TEXT(stored=True),
        content=fields.TEXT(stored=True),
        tags=fields.TEXT(stored=True),
        tags_keyword=fields.KEYWORD(stored=True),
    )

    if not os.path.exists(index_dir):
        Path(index_dir).resolve().mkdir(parents=True, exist_ok=True)

    ix = index.create_in(index_dir, schema)
    ix = index.open_dir(index_dir)
    writer = ix.writer()

    return (ix, schema, writer)


def LoadSearchDataIntoWhoosh(writer, search_data):
    # add data to whoosh
    for i, doc in enumerate(search_data):
        subset = {
            "id": str(i),
            "path": doc["path"],
            "file": doc["file"],
            "title": doc["title"],
            "content": doc["content"],
            "tags": doc["tags"],
            "tags_keyword": doc["tags"],
        }
        writer.add_document(**subset)
    writer.commit()

    return search_data


def GetSearchData(path_str):
    with open(path_str, "r", encoding="utf-8") as f:
        return json.loads(f.read())


def UnzipSearchData(zip_path):
    appdir = get_obshtml_appdir_folder_path()
    appdir.mkdir(parents=True, exist_ok=True)
    searchdata_path = appdir.joinpath("search.json")

    # unzip
    with gzip.open(zip_path, "rb") as f_in:
        with open(searchdata_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    return searchdata_path


def ConvertObsidianQueryToWhooshQuery(user_query):
    query = user_query
    query = query.replace("tag:#", "tags_keyword:")
    query = query.replace("tag:", "tags:")

    query = query.replace(" -", " ANDNOT ")
    return query


def RemovePhrasesFromQueryNodes(nodes):
    keyword_fields = ["tags_keyword"]

    def rec(obj):
        if obj.is_text() and " " in obj.r():
            # node is a phrase
            if obj.fieldname in keyword_fields:
                # phrase applies to a keyword field, this isn't allowed, remove it.
                return None
        if hasattr(obj, "nodes"):
            remove_list = []
            for node in obj.nodes:
                res = rec(node)
                if res is None:
                    remove_list.append(node)
            for rn in remove_list:
                obj.nodes.remove(rn)
        return obj

    return rec(nodes)


def RemoveKeywordPhrasesFromCleanQuery(qp, clean_query):
    nodes = qp.process(clean_query)
    nodes = RemovePhrasesFromQueryNodes(nodes)
    qo = PostProcessParse(qp, nodes)
    return qo


def PostProcessParse(qp, obj, normalize=True, debug=False):
    # Converts nodes-object to query-object.
    # The nodes object is the result of qp.process(query), instead of qp.parse(query).
    # We do the process step to get the nodes, then we remove offenders, and then continue with the parsing in this
    # function to come at a query object.

    q = obj.query(qp)
    if not q:
        q = fields.query.NullQuery
    if debug:
        print("Pre-normalized query: %r" % q)

    if normalize:
        q = q.normalize()
        if debug:
            print("Normalized query: %r" % q)
    return q


class EmbeddedSearch:
    def __init__(self, json_data=None, search_data_path=None):
        index_dir = "/tmp/obs/index"
        search_data = None

        if search_data_path is not None:
            search_data_unzipped_path_str = search_data_path.resolve().as_posix()
            search_data = GetSearchData(search_data_unzipped_path_str)
        if json_data is not None:
            search_data = json.loads(json_data)

        # create setup whoosh search
        self.ix, self.schema, self.writer = InitWhoosh(index_dir)

        # load docs
        LoadSearchDataIntoWhoosh(self.writer, search_data)

    def search(self, user_query):
        output = []

        # convert user query to a format that we can use
        clean_query = ConvertObsidianQueryToWhooshQuery(user_query)

        # create query parser
        fields = ["content", "title", "path", "file", "tags", "tags_keyword"]
        qp = MultifieldParser(fields, schema=self.ix.schema, group=OrGroup)

        # parse query into query object
        qo = RemoveKeywordPhrasesFromCleanQuery(qp, clean_query)

        if qo is None:
            # parse function expectedly failed, don't return any search results
            return []

        with self.ix.searcher() as searcher:
            results = searcher.search(qo, limit=20)
            print("-" * 35, len(results), "-" * 35)

            for doc in results:
                output.append(
                    {
                        "id": doc["id"],
                        "title": doc["title"],
                        "path": doc["path"],
                        "file": doc["file"],
                        "content": doc["content"],
                        "tags": doc["tags"],
                        "matches": {
                            "content": [x for x in doc.highlights("content", top=5).split("...") if x != ""],
                            "tags": SplitTags(doc.highlights("tags", top=10)),
                            "tags_keyword": SplitTags(doc.highlights("tags_keyword", top=10)),
                            "path": doc.highlights("path"),
                        },
                    }
                )

            return output


def SplitTags(tags_string):
    # has nothing to do with obsidian tags, this means to split the html tags.
    # we will return the actual tag, which can be used for building a url, and the match html, for showing the result
    # [(tag, match), ...]

    if tags_string == "":
        return []

    chunks = []
    buffer = ""
    tag_buffer = ""
    in_tag = False
    tags_encountered = False
    for char in tags_string:
        if char == "<":
            in_tag = True
            tags_encountered = True

        if (not in_tag) and char == " ":
            if tags_encountered:
                chunks.append([buffer, tag_buffer])
            buffer = ""
            tag_buffer = ""
            tags_encountered = False
        else:
            if not in_tag:
                tag_buffer += char
            buffer += char

        if char == ">":
            in_tag = False

    if buffer != "" and tags_encountered:
        chunks.append([buffer, tag_buffer])

    return chunks


def CliEmbeddedSearch():
    # input
    query_string = None
    search_json_gzip_path = None
    search_data_path = None

    for i, v in enumerate(sys.argv):
        if v == "-q":
            if len(sys.argv) < (i + 2):
                print('No query string given.\n  Use `obsidianhtml search -q "test"` to provide input.')
                print_global_help_and_exit(1)
            query_string = sys.argv[i + 1]

        if v == "-z":
            if len(sys.argv) < (i + 2):
                print("No search data zip path given.\n  Use `obsidianhtml search -z /path/to/obs.html/data/search.json.gzip` to provide input.")
                print_global_help_and_exit(1)
            search_json_gzip_path = sys.argv[i + 1]

        if v == "-d":
            if len(sys.argv) < (i + 2):
                print("No search data json path given.\n  Use `obsidianhtml search -d /home/user/.config/obsidianhtml/search.json` to provide input.")
                print_global_help_and_exit(1)
            search_data_path = sys.argv[i + 1]

    if search_data_path is not None:
        print(f"Searching notes @ {search_data_path}")
        search_data_path = Path(search_data_path).resolve()
    elif search_json_gzip_path is not None:
        print(f"Searching notes @ {search_json_gzip_path}")
        search_data_path = UnzipSearchData(search_json_gzip_path)
        print(f"Unzipped search.json.gzip to {search_data_path}")

    if search_data_path is None:
        print("Error: no search data configured. Quitting. Use -d to provide a path to a search.json file, or -z to provide a path to a search.json.gzip file.")
        print_global_help_and_exit(1)

    if query_string is None:
        print('No query string given.\n  Use `obsidianhtml search -q "test"` to provide input.')
        print_global_help_and_exit(1)

    # Init search
    esearch = EmbeddedSearch(search_data_path)

    # Search
    print(f"Query: '{query_string}'")
    res = esearch.search(query_string)
    print(res)
