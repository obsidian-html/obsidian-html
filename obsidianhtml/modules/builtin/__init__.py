from .. import ObsidianHtmlModule

from .cleanup_temp_files import CleanupTempFilesModule
from .resource_logger import ResourceLoggerMetaModule
from .put_user_config import PutUserConfig
from .put_config import PutConfigModule

# from .parse_sysargs import ParseSysArgsModule
from .setup import SetupModule


# dummy classes for testing:


class ModuleSetupModule(ObsidianHtmlModule):
    """
    This module is responsible for setting up the environment for the module system to work.
    Currently this means making sure that the module_data folder exists
    """

    @property
    def requires(self):
        return tuple()

    @property
    def provides(self):
        return tuple()

    @property
    def alters(self):
        return tuple()

    def run(self):
        self.print("info", f"running {self.module_name}")
