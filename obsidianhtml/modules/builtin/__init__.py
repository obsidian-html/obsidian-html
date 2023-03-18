from ..base_classes.obsidianhtml_module import ObsidianHtmlModule

from .setup import SetupModule
from .load_paths import LoadPathsModule
from .load_file_tree import LoadFileTreeModule
from .cleanup_temp_files import CleanupTempFilesModule
from .resource_logger import ResourceLoggerMetaModule

builtin_module_aliases = {
    "setup_module": SetupModule,
    "load_paths": LoadPathsModule,
    "load_file_tree": LoadFileTreeModule,
    "cleanup_temp_files": CleanupTempFilesModule,
    "resource_logger": ResourceLoggerMetaModule,
}
