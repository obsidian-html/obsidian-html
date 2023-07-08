import os
import json
import yaml
import inspect

from pathlib import Path
from datetime import datetime, date

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
        if self.is_module_file and sneak == False and self.resource_rel_path not in self.module.requires_files() and self.resource_rel_path not in self.module.written_files.listing():
            # excempted methods from requirement to report reading/writing
            stack = inspect.stack()
            if stack[1][3] not in ("integrate_save", "integrate_load"):
                if len(stack) > 3 and stack[3][3] in ["write", "print"]:
                    pass
                else:
                    if len(stack) > 3:
                        print(stack[3][3])

                    raise Exception(f"ModuleMisConfiguration: Module {self.module.module_name} reads from {self.resource_rel_path} but this is not reported in self.requires.")

        # record reading the file
        # temporary: while integrate methods exist: don't report reads for the integrate save method
        if sneak == False and inspect.stack()[1][3] not in ("integrate_save",):
            self.module.read_files.add(self.resource_rel_path)

        # Handle file not existing
        if not os.path.isfile(self.path):
            if not self.allow_absent:
                raise Exception(f"File read error: Tried to read non-existent resource {self.path}. Use allow_absent=True if empty string should be returned.")
            else:
                self.contents = ""
                return self

        # open file contents
        with open(self.path, "r", encoding=self.encoding) as f:
            self.contents = f.read()

        return self

    def write(self):
        # check whether module reports writing this output
        if self.is_module_file and self.resource_rel_path not in self.module.provides_files():
            # temporary: while integrate methods exist: don't do checks for the integrate methods
            if inspect.stack()[1][3] not in ("integrate_save", "integrate_load"):
                raise Exception(f"ModuleMisConfiguration: Module {self.module.module_name} writes to {self.resource_rel_path} but this is not reported in self.provides.")

        # record writing to the file
        self.module.written_files.add(self.resource_rel_path)

        # ensure folder exists
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)

        # write file
        with open(self.path, "w", encoding=self.encoding) as f:
            f.write(self.contents)

        if self.module.gc("keep_module_file_versions"):
            # determine folder to create the versioned file in
            with open(self.module.module_data_folder + "/guid.txt", "r") as f:
                guid = f.read()
            version_files_folder = Path(self.module.module_data_folder).joinpath(f"versions/{guid}")

            # edit file name to include timestamp and module name
            version_path = version_files_folder.joinpath(Path(self.path).relative_to(self.module.module_data_folder))
            version_path = version_path.parent.joinpath(datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%z") + "_" + self.module.module_name + "__" + version_path.name)
            version_path.parent.mkdir(parents=True, exist_ok=True)

            # write versioned file
            with open(version_path, "w", encoding=self.encoding) as f:
                f.write(self.contents)

    def exists(self):
        return os.path.isfile(self.path)

    def summary(self, dependency_type):
        modfile_dependencies = self.module.modfile("modfile_dependencies.json").read(sneak=True).from_json().unwrap()
        if self.resource_rel_path not in modfile_dependencies.keys():
            return f"<internal error> could not find {self.resource_rel_path} in modfile_dependencies.json"

        if dependency_type == "provided_by":
            provides = modfile_dependencies[self.resource_rel_path][dependency_type]
            text = f"The modfile {self.resource_rel_path}"
            if len(provides) == 0:
                text = f"{text} is not provided by any built-in or configured module.\nPerhaps you have to configure a custom module?"
                return text
            else:
                text = f"{text} is provided by the following modules:"
                for modname in provides:
                    text += f"\n  - {modname}"
                return text
        else:
            return f"<internal error> dependency_type of {dependency_type} is not implemented for modfile.summary()"

        return

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
    def default(self, obj):
        if isinstance(obj, Path):
            return obj.resolve().as_posix()
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return obj.__name__
