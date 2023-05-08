import os
import json
import yaml
import inspect

from pathlib import Path

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
    def __init__(self, resource_rel_path, path, contents="", encoding="utf-8", allow_absent=False, is_module_file=True, module=None):
        self.resource_rel_path = resource_rel_path
        self.path = path
        self.contents = contents
        self.encoding = encoding

        self.is_module_file = is_module_file
        self.module = module
        # self.via_integration = via_integration # don't do provides/requires check if read/write is done in the integration step

        self.allow_absent = allow_absent

    def read(self, sneak=False):
        # check whether module reports reading this input (or has already written it)
        if (
            self.is_module_file
            and sneak == False
            and self.resource_rel_path not in self.module.requires
            and self.resource_rel_path not in self.module.written_files.listing()
        ):
            # temporary: while integrate methods exist: don't do checks for the integrate methods
            if inspect.stack()[1][3] not in ("integrate_save", "integrate_load"):
                raise Exception(
                    f"ModuleMisConfiguration: Module {self.module.module_name} reads from {self.resource_rel_path} but this is not reported in self.requires."
                )

        # record reading the file
        # temporary: while integrate methods exist: don't report reads for the integrate save method
        if sneak == False and inspect.stack()[1][3] not in ("integrate_save",):
            self.module.read_files.add(self.resource_rel_path)

        # Handle file not existing
        if not os.path.isfile(self.path):
            if not self.allow_absent:
                raise Exception(
                    f"File read error: Tried to read non-existent resource {self.path}. Use allow_absent=True if empty string should be returned."
                )
            else:
                self.contents = ""
                return self

        # open file contents
        with open(self.path, "r", encoding=self.encoding) as f:
            self.contents = f.read()

        return self

    def write(self):
        # check whether module reports writing this output
        if self.is_module_file and self.resource_rel_path not in self.module.provides:
            # temporary: while integrate methods exist: don't do checks for the integrate methods
            if inspect.stack()[1][3] not in ("integrate_save", "integrate_load"):
                raise Exception(
                    f"ModuleMisConfiguration: Module {self.module.module_name} writes to {self.resource_rel_path} but this is not reported in self.provides."
                )

        # record writing to the file
        self.module.written_files.add(self.resource_rel_path)

        # ensure folder exists
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)

        # write file
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
        self.contents = json.dumps(self._get_contents_for_export(), indent=2, cls=to_json_encoder)
        return self

    def to_yaml(self):
        self.contents = yaml.dump(self._get_contents_for_export())
        return self

    def _get_contents_for_export(self):
        if isinstance(self.contents, hash_wrap):
            return self.contents.unwrap()
        return self.contents


class to_json_encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Path):
            return o.resolve().as_posix()
        return o.__name__
