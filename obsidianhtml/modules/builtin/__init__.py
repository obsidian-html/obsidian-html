from ..base_classes.obsidianhtml_module import ObsidianHtmlModule

from .setup_module import SetupModule
from .process_config import ProcessConfigModule
from .load_paths import LoadPathsModule
from .load_file_tree import LoadFileTreeModule
from .cleanup_temp_files import CleanupTempFilesModule
from .resource_logger import ResourceLoggerMetaModule
from .html_templater import HtmlTemplaterModule
from .load_graphers import LoadGrapherModule
from .copy_vault_to_tempdirectory import VaultCopyModule
from .prepare_output_folders import PrepareOutputFoldersModule

builtin_module_aliases = {
    "setup_module": SetupModule,
    "process_config": ProcessConfigModule,
    "load_paths": LoadPathsModule,
    "load_file_tree": LoadFileTreeModule,
    "cleanup_temp_files": CleanupTempFilesModule,
    "resource_logger": ResourceLoggerMetaModule,
    "html_templater": HtmlTemplaterModule,
    "load_graphers": LoadGrapherModule,
    "copy_vault_to_tempdirectory": VaultCopyModule,
    "prepare_output_folders": PrepareOutputFoldersModule,
}
