""" The code in this file is for running a full module list
    This is still in development, for now just use run_module() from controller.py
"""


def load_module_itenary(user_config_file_path):
    """This function takes the compiled config.yml path and generates all module lists used for the module system."""

    with open(user_config_file_path, "r") as f:
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
