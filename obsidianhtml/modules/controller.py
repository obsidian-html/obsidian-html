"""This file contains all the code necessary to run a single module ad-hoc, in the most general case.
For functions to handle running a list of modules, or custom wrappers for the run_module function, see module_runner.py"""

import yaml

from . import builtin
from .lib import verbose_enough


def get_module_class(module_name, module_class_name, module_source):
    # try getting the module based on the name, in case of builtin modules
    # this saves dumb typing
    if module_source == "built-in":
        if module_name in builtin.builtin_module_aliases.keys():
            return builtin.builtin_module_aliases[module_name]
        else:
            return getattr(builtin, module_class_name)
    else:
        raise Exception("external modules not yet implemented")


class run_module_result:
    def __init__(self, module, output):
        self.output = output
        self._module = module

        self.module_is_persistent = module.persistent

    def get_module(self, optional=False):
        if self.module_is_persistent is False:
            if optional:
                return None
            raise Exception(
                "Module was requested, but the module is not persistent. Check first with run_module_result.module_is_persistent, "
                "or set run_module_result.module(optional=True) if your code expects None values."
            )
        return self._module

    def get_output(self):
        return self.output


def run_module(
    module_name=None,
    module=None,
    module_data_folder=None,
    module_class_name=None,
    meta_modules_post=None,
    method="run",
    module_source="built-in",
    pb=None,
    verbosity=None,
):
    if module is None:
        # Either needs to be set
        if module_name is None:
            raise Exception("Neither module nor module_name is set. Cannot load module.")

        # integrate with "old" pb control flow: get module_data_folder from pb, if passed in
        if pb is not None:
            if module_data_folder is None:
                if pb.module_data_folder is None:
                    module_data_folder = pb.gc("module_data_folder")
                else:
                    module_data_folder = pb.module_data_folder

        # set default verbosity level
        if verbosity is None:
            verbosity = "error"

        # instantiate module
        module_class = get_module_class(module_name, module_class_name, module_source)
        module = module_class(module_data_folder=module_data_folder, module_name=module_name)

    # integrate with "old" pb control flow: read out pb and create files in module data folder
    if pb is not None:
        module.integrate_load(pb)  # to be implemented by the module

    # run method
    if verbose_enough("info", verbosity):
        print(
            f'[ {"INFO":^5} ] module.controller.run_module() ::',
            f"{module.module_name}.{method}()",
        )
    func = getattr(module, method)
    result = func()  # to be implemented by the module

    # integrate with "old" pb control flow: read out created files in module data folder and write to pb
    if pb is not None:
        module.integrate_save(pb)

    return run_module_result(module=module, output=result)


def load_module_itenary(module_data_folder):
    """This function takes the compiled config.yml path and generates all module lists used for the module system."""

    config_file_path = module_data_folder + "/config.yml"
    with open(config_file_path, "r") as f:
        module_cfg = yaml.safe_load(f.read())

    def hydrate_module_list(mod):
        # fill in defaults
        if "type" not in mod.keys():
            mod["type"] = "built-in"
        if "method" not in mod.keys():
            mod["method"] = "run"
        if "persistent" not in mod.keys():
            mod["persistent"] = None
        if "post_modules" not in mod.keys():
            mod["post_modules"] = []
        if "pre_modules" not in mod.keys():
            mod["pre_modules"] = []
        if "post_modules_blacklist" not in mod.keys():
            mod["post_modules_blacklist"] = []
        if "pre_modules_blacklist" not in mod.keys():
            mod["pre_modules_blacklist"] = []
        if "module" not in mod.keys():
            mod["module"] = None

        # get actual class instead of string
        mod["module"] = get_module_class(
            module_name=mod["name"],
            module_class_name=mod["module"],
            module_source=mod["type"],
        )

    for mod in module_cfg["modules"]:
        hydrate_module_list(mod)
    for mod in module_cfg["meta_modules_post"]:
        hydrate_module_list(mod)

    return (module_cfg["modules"], module_cfg["meta_modules_post"])
