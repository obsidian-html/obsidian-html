""" The code in this file is for running a full module list
    This is still in development, for now just use run_module() from controller.py
"""

import yaml
from .controller import get_module_class, run_module
from .lib import verbose_enough


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

    return result


def run_modules(modules, meta_modules_post, module_data_folder, verbosity):
    instantiated_modules = {}

    for listing in modules:
        # Run modules
        # ------------------------
        # instantiate module
        module_obj = instantiate_module(
            module_class=listing["module"],
            module_name=listing["name"],
            persistent=listing["persistent"],
            instantiated_modules=instantiated_modules,
            module_data_folder=module_data_folder,
            verbosity=verbosity,
        )

        # run method
        method = listing["method"]
        if verbose_enough("info", verbosity):
            print(
                f'[ {"INFO":^5} ] module.controller.run_modules() ::',
                f"{listing['name']}.{method}()",
            )
        result = getattr(module_obj, method)()

        # Run post meta modules
        # ------------------------
        run_post_modules(
            meta_modules_post,
            module_obj,
            module_run_result=result,
            instantiated_modules=instantiated_modules,
            module_data_folder=module_data_folder,
            verbosity=verbosity,
        )


def run_post_modules(
    meta_modules_post,
    module_obj,
    module_run_result,
    instantiated_modules,
    module_data_folder,
    verbosity,
):
    for listing in meta_modules_post:
        # instantiate module
        meta_module_obj = instantiate_module(
            module_class=listing["module"],
            module_name=listing["name"],
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
        result = getattr(meta_module_obj, method)(module=module_obj, result=module_run_result)


def instantiate_module(
    module_class,
    module_name,
    instantiated_modules,
    persistent,
    module_data_folder,
    verbosity="deprecation",
    level=0,
):
    """This function instantiates modules, and stores the resulting object, so that it can be retrieved when persistence is enabled on the module"""
    if persistent == True and module_class.__name__ in instantiated_modules:
        if verbose_enough("debug", verbosity):
            print(
                f'[ {"DEBUG":^5} ] {"* "*level}module.controller.instantiate_module :: reuse of persistent module:',
                module_name,
            )
        module_obj = instantiated_modules[module_class.__name__]
    else:
        if verbose_enough("debug", verbosity):
            print(
                f'[ {"DEBUG":^5} ] {"* "*level}module.controller.instantiate_module :: instantiation of module: ',
                module_name,
            )
        module_obj = module_class(module_data_folder=module_data_folder, module_name=module_name)
        instantiated_modules[module_class.__name__] = module_obj

    return module_obj
