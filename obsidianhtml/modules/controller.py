"""This file contains all the code necessary to run a module."""
import sys
import yaml
import importlib

from pathlib import Path

from . import builtin
from .lib import verbose_enough


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
    method="run",
    meta_modules_post=None,
    instantiated_modules=None,
    persistent=None,
    module_source=None,
    module_binary=None,
    pb=None,
    verbosity="error",
):
    # INSTANTIATE MODULE
    # ==================================================
    module, module_class = get_module(
        module=module,
        module_name=module_name,
        module_class_name=module_class_name,
        module_source=module_source,
        module_binary=module_binary,
        module_run_method=method,
        persistent=persistent,
        instantiated_modules=instantiated_modules,
        module_data_folder=module_data_folder,
        verbosity=verbosity,
    )

    # RUN MODULE
    # ==================================================
    # integrate with "old" pb control flow: read out pb and create files in module data folder
    if pb is not None:
        module.integrate_load(pb)

    # check that required modfiles are present
    getattr(module, "check_required_modfiles_exist")()

    # check if method should be run, otherwise, cancel further execution
    # - note that module.integrate_load is always run, as this might provide information required
    #   by module.accept() to determine if the module should run or not.
    accept = getattr(module, "accept")
    if accept(module_data_folder) == False:
        return None

    # run method
    if verbose_enough("info", verbosity):
        print(
            f'[ {"INFO":^5} ] module.controller.run_module() ::',
            f"{module.module_name}.{method}()",
        )
    module_dot_method = getattr(module, method)

    # import time
    # start_time = time.perf_counter ()

    result = module_dot_method()

    # end_time = time.perf_counter ()
    # print(end_time - start_time, "seconds")

    # convert basic result to run_module_result() type to manage different module outputs in an organized fashion
    result = run_module_result(module=module, output=result)

    # integrate with "old" pb control flow: read out created files in module data folder and write to pb
    if pb is not None:
        module.integrate_save(pb)

    # RUN POST-MODULES
    # ==================================================
    run_post_modules(
        meta_modules_post,
        module,
        module_run_result=result,
        instantiated_modules=instantiated_modules,
        module_data_folder=module_data_folder,
        verbosity=verbosity,
    )

    return result


def run_post_modules(
    meta_modules_post,
    module_obj,
    module_run_result,
    instantiated_modules,
    module_data_folder,
    verbosity,
):
    if meta_modules_post is None:
        return None

    for listing in meta_modules_post:
        # instantiate module
        meta_module_obj = instantiate_module(
            module_class=listing["module"],
            module_name=listing["name"],
            module_binary=listing["binary"],
            module_run_method=listing["method"],
            persistent=listing["persistent"],
            instantiated_modules=instantiated_modules,
            module_data_folder=module_data_folder,
            verbosity=verbosity,
            level=1,
        )

        # don't run if blacklisted
        if not module_obj.allow_post_module(meta_module_obj):
            if verbose_enough("debug", verbosity):
                print(
                    f'[ {"DEBUG":^5} ] * module.controller.run_post_module ::',
                    f"SKIPPED running post-module [{listing['name']}]; blacklisted by module [{module_obj.__class__.__name__}]",
                )
            continue

        # run method
        method = listing["method"]
        if verbose_enough("debug", verbosity):
            print(
                f'[ {"DEBUG":^5} ] * module.controller.run_post_module ::',
                f"{listing['name']}.{method}()",
            )
        result = getattr(meta_module_obj, method)(module=module_obj, run_module_result=module_run_result)


def get_module(
    module=None,
    module_name=None,
    module_class_name=None,
    module_data_folder=None,
    module_source=None,
    module_binary=None,
    module_run_method="run",
    persistent=None,
    instantiated_modules=None,
    verbosity=None,
):
    """Convenience function. Will either return the module from instantiated_modules, if present and the module is persistent,
    or it will call upon instantiate_module() to instantiate the module for us."""

    if module is not None:
        return module

    # Either module_name or module needs to be set
    if module_name is None:
        raise Exception("Neither module nor module_name is set. Cannot load module.")

    # instantiate module
    module_class = get_module_class(module_name, module_class_name, module_source)
    module = instantiate_module(
        module_class=module_class,
        module_name=module_name,
        module_binary=module_binary,
        module_run_method=module_run_method,
        instantiated_modules=instantiated_modules,
        persistent=persistent,
        module_data_folder=module_data_folder,
        verbosity=verbosity,
    )

    return module, module_class


def get_module_class(module_name, module_class_name, module_source):
    # try getting the module based on the name, in case of builtin modules
    # this saves dumb typing
    if module_source == None:
        if module_name in builtin.builtin_module_aliases.keys():
            return builtin.builtin_module_aliases[module_name]
        elif module_class_name in builtin.builtin_module_aliases.keys():
            return builtin.builtin_module_aliases[module_class_name]
        else:
            raise Exception(f"Could not find match for module {module_name} ({module_class_name}) in the modules/builtin directory. " + "Is the module class imported in modules/builtin/__init__.py ?")
    else:
        # get module from file
        module_path = Path(module_source)
        sys.path.insert(1, module_path.parent.as_posix())
        module_module = importlib.import_module(module_path.stem, package=None)

        if module_class_name is None:
            return getattr(module_module, "export_module_class")()
        else:
            return getattr(module_module, module_class_name)


def instantiate_module(
    module_class,
    module_name,
    module_binary,
    module_run_method,
    instantiated_modules,
    module_data_folder,
    persistent=None,
    verbosity="deprecation",
    level=0,
):
    """This function instantiates modules, and stores the resulting object, so that it can be retrieved when persistence is enabled on the module. This
    function also stores the instantiated modules when persistence is set to true."""
    module_obj = None

    # REUSE
    # ---
    if instantiated_modules is not None:
        if persistent == True and module_class.__name__ in instantiated_modules:
            if verbose_enough("debug", verbosity):
                print(
                    f'[ {"DEBUG":^5} ] {"* "*level}module.controller.instantiate_module :: reuse of persistent module:',
                    module_name,
                )

            return instantiated_modules[module_class.__name__]

    # CREATE
    # ---
    if verbose_enough("debug", verbosity):
        print(
            f'[ {"DEBUG":^5} ] {"* "*level}module.controller.instantiate_module :: instantiation of module: ',
            module_name,
        )
    module_obj = module_class(module_data_folder=module_data_folder, module_name=module_name, persistent=persistent)

    if module_binary is not None:
        module_obj.set_binary(module_binary, module_run_method)
        module_obj.test_module_validity()
    else:
        module_obj.test_module_validity()
        module_obj.try_load_mod_config()

    # STORE
    # ---
    if instantiated_modules is not None and module_obj.persistent == True:
        instantiated_modules[module_class.__name__] = module_obj

    return module_obj


def load_module_itenary(module_data_folder):
    """This function takes the compiled config.yml path and generates all module lists used for the module system."""

    config_file_path = module_data_folder + "/config.yml"
    with open(config_file_path, "r") as f:
        module_cfg = yaml.safe_load(f.read())

    def hydrate_module_listing(mod):
        # fill in defaults
        mod["type"] = "built-in"

        if "binary" in mod.keys():
            mod["type"] = "binary"
            mod["module_class"] = "binary"
        else:
            mod["binary"] = None

        if "file" in mod.keys():
            mod["type"] = "external"
        else:
            mod["file"] = None

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
        if "module_class" not in mod.keys():
            mod["module_class"] = None

        # get actual class instead of string
        mod["module"] = get_module_class(module_name=mod["name"], module_class_name=mod["module_class"], module_source=mod["file"])

    for phase in module_cfg["module_list"].keys():
        for mod in module_cfg["module_list"][phase]:
            hydrate_module_listing(mod)

    for mod in module_cfg["meta_modules_post"]:
        hydrate_module_listing(mod)

    # for mod in module_cfg["modules"]:
    #     hydrate_module_list(mod)
    # for mod in module_cfg["meta_modules_post"]:
    #     hydrate_module_list(mod)

    return (module_cfg["module_list"], module_cfg["meta_modules_post"])


def run_module_setup(pb=None):
    """Runs the setup module, which creates the module data folder, and places the arguments.yml and config.yml files there.
    Normally, modules don't return anything, if they do, that means they failed. In this special case we need to get the module data folder back.
    """

    result = run_module(module_name="setup_module", module_data_folder="/tmp", pb=pb)

    # Now that the setup_module is done running, we quickly get the verbosity value from it so that we can print the logging.
    # (Normally we'd use result.get_module(), but the setup_module is not meant to be persistent, so this method would give either None
    # or an error)
    module = result._module
    if verbose_enough("info", module.verbosity):
        print(
            f'[ {"INFO":^5} ] module.runner.run_module_setup() ::',
            "setup_module.run() (finished running)",
        )

    return result, module
