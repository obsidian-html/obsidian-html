import shutil
from . import Types as T
from ..lib import is_installed

import os
import tempfile             # used to create temporary files/folders
from subprocess import Popen, PIPE
from time import sleep

class Optional:
    @staticmethod
    def remove_previous_obsidianhtml_output(pb) -> T.SystemChange:
        if pb.gc('toggles/no_clean', cached=True) == False:
            print('> CLEARING OUTPUT FOLDERS')
            if pb.gc('toggles/compile_md', cached=True):
                if pb.paths['md_folder'].exists():
                    shutil.rmtree(pb.paths['md_folder'])

            if pb.paths['html_output_folder'].exists():
                shutil.rmtree(pb.paths['html_output_folder'])    

def create_obsidianhtml_output_folders(pb) -> T.SystemChange:
    print('> CREATING OUTPUT FOLDERS')
    # create markdown output folder
    if pb.gc('toggles/compile_md', cached=True):
        pb.paths['md_folder'].mkdir(parents=True, exist_ok=True)
    # create html output folders
    pb.paths['html_output_folder'].mkdir(parents=True, exist_ok=True)
    # create logging output folders
    if pb.gc('toggles/extended_logging', cached=True):
        pb.paths['log_output_folder'].mkdir(parents=True, exist_ok=True)
        pb.paths['log_output_folder'] = pb.paths['log_output_folder'].resolve()
