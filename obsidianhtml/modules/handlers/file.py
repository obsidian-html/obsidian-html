import os
import json
import yaml

from ..lib import hash_wrap

"""
Read:
- File(path=path).read().text()
- File(path=path).read().from_json()
Write:
- File(path=path, contents=contents).write()
- File(path=path, contents=contents).to_json().write()
"""


class File:
    def __init__(self, path, contents="", encoding="utf-8", allow_absent=False):
        self.contents = contents
        self.path = path
        self.encoding = encoding
        self.allow_absent = False

    def read(self):
        if not os.path.isfile(self.path):
            if not self.allow_absent:
                raise Exception(f"File read error: Tried to read non-existent resource {path}. Use allow_absent=True if empty string should be returned.")
            else:
                self.contents = ""
        with open(self.path, "r", encoding=self.encoding) as f:
            self.contents = f.read()

        return self

    def write(self):
        with open(self.path, "w", encoding=self.encoding) as f:
            f.write(self.contents)

    # --- read contents
    def text(self):
        return self.contents

    def from_json(self):
        if self.contents == "" or self.contents is None:
            return None
        obj = json.loads(self.contents)
        if isinstance(obj, dict):
            return hash_wrap(obj)
        return obj

    def from_yaml(self):
        if self.contents == "" or self.contents is None:
            return None
        obj = yaml.safe_load(self.contents)
        if isinstance(obj, dict):
            return hash_wrap(obj)
        return obj

    # --- export contents
    def to_json(self):
        self.contents = json.dumps(self.contents, indent=2, cls=to_json_encoder)
        return self

    def to_yaml(self):
        self.contents = yaml.dump(self.contents)
        return self


class to_json_encoder(json.JSONEncoder):
    def default(self, o):
        return o.__name__
