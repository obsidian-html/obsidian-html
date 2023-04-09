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


def run_module(module_name=None, module=None, module_data_folder=None, module_class_name=None, method="run", module_source="built-in", pb=None, verbosity=None):
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


def run_module_setup(pb=None):
    """Runs the setup module, which creates the module data folder, and places the arguments.yml and config.yml files there.
    Normally, modules don't return anything, if they do, that means they failed. In this special case we need to get the module data folder back.
    """

    result = run_module(module_name="setup_module", module_data_folder="/tmp", pb=pb)

    # Now that the setup_module is done running, we quickly get the verbosity value from it so that we can print the logging.
    # (Normally we'd use result.get_module(), but the setup_module is not meant to be persistent, so this method would give either None
    # or an error)
    module = result._module
    if verbose_enough('info', module.verbosity):
        print(
            f'[ {"INFO":^5} ] module.controller.run_module_setup() ::',
            "setup_module.run() (finished running)",
        )

    return result
