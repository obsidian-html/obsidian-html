from typing import Dict, List, Sequence

import os, os.path
import sys
import json
import gzip
import shutil

from pathlib import Path

from whoosh import index
from whoosh.qparser import QueryParser
from whoosh.fields import *

from .lib import    print_global_help_and_exit, get_obshtml_appdir_folder_path


def InitWhoosh(index_dir):
    schema = Schema(
        rtr_url=ID(stored=True),
        url=STORED,
        title=TEXT(stored=True),
        md=TEXT(stored=True),
        keywords=KEYWORD(stored=True, scorable=True),
        tags=KEYWORD(stored=True, scorable=True)
    )

    if not os.path.exists(index_dir):
        Path(index_dir).resolve().mkdir(parents=True, exist_ok=True)

    ix = index.create_in(index_dir, schema)
    ix = index.open_dir(index_dir)
    writer = ix.writer()

    return (ix, schema, writer)

def LoadSearchDataIntoWhoosh(writer, search_data_unzipped_path_str):
    # read in json
    search_data = GetSearchData(search_data_unzipped_path_str)

    # add data to whoosh
    for doc in search_data:
        writer.add_document(**doc)
    writer.commit()

    return search_data

def GetSearchData(path_str):
    with open(path_str, 'r', encoding='utf-8') as f:
        return json.loads(f.read())

def UnzipSearchData(zip_path):
    appdir = get_obshtml_appdir_folder_path()
    appdir.mkdir(parents=True, exist_ok=True)
    searchdata_path = appdir.joinpath('search.json')

    # unzip
    with gzip.open(zip_path, 'rb') as f_in:
        with open(searchdata_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    return searchdata_path

class EmbeddedSearch:
    def __init__(self, search_data_path):
        search_data_unzipped_path_str = search_data_path.resolve().as_posix()
        index_dir = '/tmp/obs/index'

        # create setup whoosh search
        self.ix, self.schema, self.writer = InitWhoosh(index_dir)

        # load docs
        search_data = LoadSearchDataIntoWhoosh(self.writer, search_data_unzipped_path_str)

    def search(self, phrase):
        qp = QueryParser("md", schema=self.ix.schema)
        q = qp.parse(phrase)

        with self.ix.searcher() as searcher:
            results = searcher.search(q, limit=None)
            print('-'*35, len(results), '-'*35)

            for doc in results:
                print(doc['title'])

def CliEmbeddedSearch():
    # input
    query_string = None
    search_json_gzip_path = None
    search_data_path = None

    for i, v in enumerate(sys.argv):
        if v == '-q':
            if len(sys.argv) < (i + 2):
                print(f'No query string given.\n  Use `obsidianhtml search -q "test"` to provide input.')
                print_global_help_and_exit(1)
            query_string = sys.argv[i+1]

        if v == '-z':
            if len(sys.argv) < (i + 2):
                print(f'No search data zip path given.\n  Use `obsidianhtml search -z /path/to/obs.html/data/search.json.gzip` to provide input.')
                print_global_help_and_exit(1)
            search_json_gzip_path = sys.argv[i+1]

        if v == '-d':
            if len(sys.argv) < (i + 2):
                print(f'No search data json path given.\n  Use `obsidianhtml search -d /home/user/.config/obsidianhtml/search.json` to provide input.')
                print_global_help_and_exit(1)
            search_data_path = sys.argv[i+1]

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
        print(f'No query string given.\n  Use `obsidianhtml search -q "test"` to provide input.')
        print_global_help_and_exit(1)

    # Init search 
    esearch = EmbeddedSearch(search_data_path)

    # Search
    print(f"Query: '{query_string}'")
    esearch.search(query_string)