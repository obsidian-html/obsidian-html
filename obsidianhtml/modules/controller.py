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
    def __init__(self, result, module):
        self.value = result
        self.module = module

    @property
    def module_is_persistent(self):
        """Will return True if module is returned (and thus persistent), otherwise False"""
        if self.module is not None:
            return True
        return False

    @property
    def module(self):
        if module is None:
            raise Exception(
                "Module was requested, but none was returned. This means that the module was not set to persistent."
                "Check using result.module_is_persistent before addressing the module."
            )


def run_module(
    module_name,
    module_data_folder=None,
    module_class_name=None,
    method="run",
    module_source="built-in",
    pb=None,
    verbosity=None,
):
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
            f"{module_name}.{method}()",
        )
    func = getattr(module, method)
    result = func()  # to be implemented by the module

    # integrate with "old" pb control flow: read out created files in module data folder and write to pb
    if pb is not None:
        module.integrate_save(pb)

    if module.persistent == True:
        return (result, module)

    return (result, None)


def run_module_setup(pb=None):
    """Runs the setup module, which creates the module data folder, and places the arguments.yml and config.yml files there.
    Normally, modules don't return anything, if they do, that means they failed. In this special case we need to get the module data folder back.
    """
    print(
        f'[ {"INFO":^5} ] module.controller.run_module_setup() ::',
        f"setup_module.run()",
    )
    return run_module(module_name="setup_module", module_data_folder="/tmp", pb=pb)
