import os
from .. import ObsidianHtmlModule

class CleanupTempFilesModule(ObsidianHtmlModule):
    """
    This module will remove all temporary files after we are done running.
    """
    @property
    def requires(self):
        return tuple()
    @property
    def provides(self):
        return tuple(['config.yml'])
    @property
    def alters(self):
        return tuple()

    def allow_post_module(self, meta_module):
        """ Return True if post module is allowed to run after this one, else return False """
        if meta_module.module_class_name in ['ResourceLoggerMetaModule']:
            return False
        return True

    def run(self):
        for resource in ['log.resources']:
            path = self.path(resource)
            if os.path.isfile(path):
                self.print('info', f'removing {path}')
                os.remove(path) 
