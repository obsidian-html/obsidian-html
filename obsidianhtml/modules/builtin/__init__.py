from ..base_classes.obsidianhtml_module import ObsidianHtmlModule

from .setup_module import SetupModule
from .apply_cmdline_arguments import ApplyCommandlineArgumentsModule
from .process_config import ProcessConfigModule, ProcessConfigAutoModule
from .load_paths import LoadPathsModule
from .get_file_list import GetFileListModule
from .cleanup_temp_files import CleanupTempFilesModule
from .resource_logger import ResourceLoggerMetaModule
from .html_templater import HtmlTemplaterModule
from .load_graphers import LoadGrapherModule
from .copy_vault_to_tempdirectory import VaultCopyModule
from .prepare_output_folders import PrepareOutputFoldersModule
from .parse_metadata import ParseMetadataModule
from .filter_on_metadata import FilterOnMetadataModule
from .binary import BinaryModule
from .stop import StopModule

builtin_module_aliases = {
    "setup_module": SetupModule,
    "process_config": ProcessConfigModule,
    "load_paths": LoadPathsModule,
    "process_config_auto": ProcessConfigAutoModule,
    "get_file_list": GetFileListModule,
    # "cleanup_temp_files": CleanupTempFilesModule,
    "resource_logger": ResourceLoggerMetaModule,
    "html_templater": HtmlTemplaterModule,
    "load_graphers": LoadGrapherModule,
    "copy_vault_to_tempdirectory": VaultCopyModule,
    "prepare_output_folders": PrepareOutputFoldersModule,
    "parse_metadata": ParseMetadataModule,
    "filter_on_metadata": FilterOnMetadataModule,
    "binary": BinaryModule,
    "stop": StopModule,
    "apply_cmdline_arguments": ApplyCommandlineArgumentsModule,
}
