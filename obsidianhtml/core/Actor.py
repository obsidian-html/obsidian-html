import shutil


from ..core.CopyVault import CreateTemporaryCopy

from . import Types as T


class Optional:
    @staticmethod
    def copy_vault_to_tempdir(pb):
        """Creates a temporary folder and copies the user's vault to that folder.
        This is so that we don't mess anything up in the user's vault.
        Make sure to keep passing the tmpdir object up the stack. If you don't the folder will be deleted
        when the function ends.
        """
        if pb.gc("copy_vault_to_tempdir") and pb.gc("toggles/compile_md"):
            # Copy over vault to tempdir
            tmpdir = CreateTemporaryCopy(source_folder_path=pb.paths["obsidian_folder"], pb=pb)
            pb.update_paths(reason="using_tmpdir", tmpdir=tmpdir)
            pb.jars["tmpdir"] = tmpdir  # store so that the reference remains in memory and the folder is not instantly deleted!


