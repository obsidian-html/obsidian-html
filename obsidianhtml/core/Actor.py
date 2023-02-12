import shutil


from ..core.CopyVault import CreateTemporaryCopy

from . import Types as T



class Optional:
    @staticmethod
    def copy_vault_to_tempdir(pb):
        ''' Creates a temporary folder and copies the user's vault to that folder.
            This is so that we don't mess anything up in the user's vault.
            Make sure to keep passing the tmpdir object up the stack. If you don't the folder will be deleted
            when the function ends. 
        '''
        if pb.gc('copy_vault_to_tempdir') and pb.gc('toggles/compile_md'):
            # Copy over vault to tempdir
            tmpdir = CreateTemporaryCopy(source_folder_path=pb.paths['obsidian_folder'], pb=pb)
            pb.update_paths(reason='using_tmpdir', tmpdir=tmpdir)

            return tmpdir # return so that the folder is not instantly deleted!

    @staticmethod
    def remove_previous_obsidianhtml_output(pb) -> T.SystemChange:
        ''' Cleanup the result of the previous run (md and html folders) '''

        if pb.gc('toggles/no_clean', cached=True) is False:
            print('> CLEARING OUTPUT FOLDERS')
            if pb.gc('toggles/compile_md', cached=True):
                if pb.paths['md_folder'].exists():
                    shutil.rmtree(pb.paths['md_folder'])

            if pb.paths['html_output_folder'].exists():
                shutil.rmtree(pb.paths['html_output_folder'])    

def create_obsidianhtml_output_folders(pb) -> T.SystemChange:
    ''' We need to ensure that the folders that we write our markdown and html to exist. '''

    if pb.gc('toggles/compile_md', cached=True) or pb.gc('toggles/compile_html', cached=True):
        print('> CREATING OUTPUT FOLDERS')

    # create markdown output folder
    if pb.gc('toggles/compile_md', cached=True):
        pb.paths['md_folder'].mkdir(parents=True, exist_ok=True)

    # create html output folders
    if pb.gc('toggles/compile_html', cached=True):
        pb.paths['html_output_folder'].mkdir(parents=True, exist_ok=True)
    
    # create logging output folders
    if pb.gc('toggles/extended_logging', cached=True):
        pb.paths['log_output_folder'].mkdir(parents=True, exist_ok=True)
        pb.paths['log_output_folder'] = pb.paths['log_output_folder'].resolve()
