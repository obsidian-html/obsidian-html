import yaml
import shutil
import os
import glob
import tempfile

from subprocess import Popen, PIPE
from pathlib import Path

from ..base_classes import ObsidianHtmlModule
from ...lib import is_installed, pushd, should_ignore


class VaultCopyModule(ObsidianHtmlModule):
    """Creates a temporary folder and copies the user's vault to that folder.
    This is so that we don't mess anything up in the user's vault.
    Make sure to keep passing the tmpdir object up the stack. If you don't the folder will be deleted
    when the function ends.
    """

    @staticmethod
    def requires():
        return tuple(["config.yml", "paths.json", "index/files.json"])

    @staticmethod
    def provides():
        return tuple(["paths.json", "index/files.json"])

    @staticmethod
    def alters():
        return tuple()

    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def integrate_save(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        # update paths
        paths = self.retrieve("paths")
        pb.paths["obsidian_folder"] = paths["obsidian_folder"]
        pb.paths["obsidian_entrypoint"] = paths["obsidian_entrypoint"]
        pb.paths["original_obsidian_folder"] = paths["original_obsidian_folder"]
        pb.paths["original_obsidian_entrypoint"] = paths["original_obsidian_entrypoint"]

    def accept(self, module_data_folder):
        """This function is run before run(), if it returns False, then the module run is skipped entirely. Any other value will be accepted"""
        if not self.gc("copy_vault_to_tempdir"):
            return False
        if not self.gc("toggles/compile_md"):
            return False

    def run(self):
        if not self.gc("copy_vault_to_tempdir"):
            return
        if not self.gc("toggles/compile_md"):
            return

        # load input
        paths = self.modfile("paths.json").read().from_json()
        for key, value in paths.items():
            paths[key] = Path(value)

        # Remove tmpdir if exists, then recreate tmpdir
        tmpdir = paths["appdir"].joinpath("tmpdir/input/").resolve()
        if tmpdir.exists():
            shutil.rmtree(tmpdir)
        tmpdir.mkdir(parents=True, exist_ok=True)

        # Update paths to use new tmpdir
        self.print("DEBUG", "Overwriting paths: obsidian_folder, obsidian_entrypoint, input_folder")

        paths["original_obsidian_folder"] = paths["obsidian_folder"]
        paths["original_obsidian_entrypoint"] = paths["obsidian_entrypoint"]

        paths["obsidian_folder"] = tmpdir
        paths["obsidian_entrypoint"] = paths["obsidian_folder"].joinpath(paths["rel_obsidian_entrypoint"])

        if self.gc("toggles/compile_md"):
            paths["original_input_folder"] = paths["original_obsidian_folder"]
            paths["input_folder"] = paths["obsidian_folder"]
            paths["entrypoint"] = paths["obsidian_entrypoint"]

        self.store("paths", paths)
        self.modfile("paths.json", paths).to_json().write()

        # Copy vault from original location to new location
        files = self.modfile("index/files.json").read().from_json()
        new_files = []
        source_folder_path = paths["original_obsidian_folder"]
        target_folder_path = paths["obsidian_folder"]
        for file in files:
            src_path = Path(file)
            rel_path = src_path.relative_to(source_folder_path)
            dst_path = target_folder_path.joinpath(rel_path)

            new_files.append(dst_path)
            self.copy_file(src_path, dst_path)

        # update index/files.json
        self.modfile("index/files.json", new_files).to_json().write()

    def copy_file(self, src_path, dst_path):
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        with open(src_path, "rb") as r:
            with open(dst_path, "wb") as w:
                w.write(r.read())

    # def copy_vault_to_tmpdir(self):
    #     paths = self.retrieve("paths")
    #     source_folder_path=paths["original_obsidian_folder"]
    #     target_folder_path=paths["obsidian_folder"]

    #     self.print("INFO", f"COPYING VAULT {source_folder_path} TO {target_folder_path}")

    #     # Decide which method to use
    #     copy_method = self.gc("copy_vault_to_tempdir_method")

    #     if copy_method == "default":
    #         if is_installed("rsync"):
    #             copy_method = "rsync"
    #         else:
    #             copy_method = "shutil"

    #     if self.gc("copy_vault_to_tempdir_method") == "rsync":
    #         if is_installed("rsync"):
    #             copy_method = "rsync"
    #         else:
    #             self.print(
    #                 "WARNING",
    #                 "copy_vault_to_tempdir_method was set to rsync, but rsync is not present on the system. Defaulting to shutil copy method."
    #             )
    #             copy_method = "shutil"

    #     # Call copytree function (rsync)
    #     if copy_method == "rsync":
    #         self.copy_tree_rsync(
    #             source_folder_path.as_posix(),
    #             target_folder_path.as_posix(),
    #             exclude=self.gc("exclude_glob"),
    #             verbose=self.gc("copy_vault_to_tempdir_follow_copy"),
    #         )

    #     # Catch invalid settings
    #     elif copy_method not in ["shutil", "shutil_walk"]:
    #         raise Exception(f"Copy method of {copy_method} not known.")
    #     else:
    #         # Compile ignore list
    #         excluded_paths = []
    #         if isinstance(self.gc("exclude_glob", cached=True), list):
    #             owd = pushd(source_folder_path)  # move working dir to root dir (needed for glob)
    #             for line in self.gc("exclude_glob", cached=True):
    #                 excluded_paths += glob.glob(line, recursive=True)
    #             excluded_paths = [Path(x) for x in excluded_paths]
    #             self.print("DEBUG", "Paths that will be ignored:", [x.as_posix() for x in excluded_paths])
    #             os.chdir(owd)

    #         # Call copytree function (shutil_walk or shutil)
    #         if self.gc("copy_vault_to_tempdir_method") == "shutil_walk":
    #             self.copytree_shutil_walk(source_folder_path, target_folder_path, ignore=excluded_paths, follow_copy=self.gc("copy_vault_to_tempdir_follow_copy"))
    #         else:
    #             self.copytree_shutil(source_folder_path, target_folder_path, ignore=excluded_paths, follow_copy=self.gc("copy_vault_to_tempdir_follow_copy"))

    #     self.print("INFO", "COPYING VAULT: Done")

    # def copy_tree_rsync(self, src_dir, dst_dir, exclude, verbose=False):
    #     # Get relative ignore paths
    #     exclude_list = []
    #     for path in exclude:
    #         exclude_list += ["--exclude", path]

    #     # compile command
    #     if src_dir[-1] != "/":
    #         src_dir += "/"
    #     if dst_dir[-1] == "/":
    #         dst_dir = dst_dir[:-1]

    #     if verbose:
    #         settings = "-av"
    #     else:
    #         settings = "-a"

    #     command = ["rsync", settings, src_dir, dst_dir] + exclude_list

    #     self.print("debug", f'running: {" ".join(command)}')

    #     # run command
    #     p = Popen(command, stdout=PIPE, stderr=PIPE)
    #     output, error = p.communicate()
    #     if p.returncode != 0:
    #         self.print("error", "Copy failed %d %s %s" % (p.returncode, output.decode("utf-8").replace("\\n", "\n"), error))
    #     else:
    #         self.print("debug", "Copy succeeded %d %s %s" % (p.returncode, output.decode("utf-8").replace("\\n", "\n"), error))

    # def copytree_shutil(self, src, dst, symlinks=False, follow_copy=False, ignore=None, copy_function=shutil.copy, ignore_dangling_symlinks=False):
    #     names = os.listdir(src)

    #     os.makedirs(dst, exist_ok=True)
    #     errors = []

    #     for name in names:
    #         srcname = os.path.join(src, name)
    #         dstname = os.path.join(dst, name)

    #         if should_ignore(ignore, Path(srcname)):
    #             continue

    #         if follow_copy:
    #             self.print("debug", "copy: ", srcname)
    #         try:
    #             if os.path.islink(srcname):
    #                 linkto = os.readlink(srcname)
    #                 if symlinks:
    #                     os.symlink(linkto, dstname)
    #                 else:
    #                     # ignore dangling symlink if the flag is on
    #                     if not os.path.exists(linkto) and ignore_dangling_symlinks:
    #                         continue
    #                     # otherwise let the copy occurs. copy2 will raise an error
    #                     copy_function(srcname, dstname)
    #             elif os.path.isdir(srcname):
    #                 self.copytree_shutil(srcname, dstname, symlinks, follow_copy=follow_copy, ignore=ignore, copy_function=copy_function, ignore_dangling_symlinks=ignore_dangling_symlinks)
    #             else:
    #                 # Will raise a SpecialFileError for unsupported file types
    #                 copy_function(srcname, dstname)
    #         # catch the Error from the recursive copytree so that we can
    #         # continue with other files
    #         except Exception as err:
    #             print(err)
    #             errors.extend(err.args[0])
    #         except EnvironmentError as why:
    #             errors.append((srcname, dstname, str(why), "copyfile error"))
    #     try:
    #         shutil.copystat(src, dst)
    #     except OSError as why:
    #         if WindowsError is not None and isinstance(why, WindowsError):
    #             # Copying file access times may fail on Windows
    #             pass
    #         else:
    #             errors.extend((src, dst, str(why), "copystat error"))
    #     if errors:
    #         raise Exception("".join(errors))

    # def copytree_shutil_walk(self, src, dst, symlinks=False, follow_copy=False, ignore=None, copy_function=shutil.copy, ignore_dangling_symlinks=False):

    #     errors = []

    #     for root, dirs, files in os.walk(src, topdown=True):
    #         for name in files:
    #             # Set paths
    #             file_src_path = Path(os.path.join(root, name)).resolve()
    #             file_dst_path = Path(dst).resolve().joinpath(file_src_path.relative_to(pb.paths["obsidian_folder"]))
    #             file_dst_folder_path = file_dst_path.parent

    #             # Ignore if file is excluded or in an excluded folder (see exclude_subfolders)
    #             if should_ignore(ignore, file_src_path):
    #                 continue

    #             # Get strings of path objects
    #             file_src_path_str = file_src_path.as_posix()
    #             file_dst_path_str = file_dst_path.as_posix()
    #             file_dst_folder_path_str = file_dst_folder_path.as_posix()

    #             # Create folder if it does not exist
    #             os.makedirs(file_dst_folder_path_str, exist_ok=True)

    #             # Copy file over
    #             if follow_copy:
    #                 self.print("DEBUG", "copy: ", file_src_path_str)
    #             try:
    #                 if file_src_path.is_symlink():
    #                     linkto = file_src_path.readlink()
    #                     if symlinks:
    #                         os.symlink(linkto, file_dst_path_str)
    #                     else:
    #                         # ignore dangling symlink if the flag is on
    #                         if not os.path.exists(linkto) and ignore_dangling_symlinks:
    #                             continue
    #                         # otherwise let the copy occurs. copy2 will raise an error
    #                         copy_function(file_src_path_str, file_dst_folder_path_str)
    #                 else:
    #                     # Will raise a SpecialFileError for unsupported file types
    #                     copy_function(file_src_path_str, file_dst_folder_path_str)

    #             # catch the Error from the recursive copytree so that we can
    #             # continue with other files
    #             except Exception as err:
    #                 print(err)
    #                 errors.extend(err.args[0])
    #             except EnvironmentError as why:
    #                 errors.append((file_src_path_str, file_dst_path_str, str(why), "copyfile error"))

    #     # Set correct permissions on target folder
    #     try:
    #         shutil.copystat(src, dst)
    #     except OSError as why:
    #         if WindowsError is not None and isinstance(why, WindowsError):
    #             # Copying file access times may fail on Windows
    #             pass
    #         else:
    #             errors.extend((file_src_path_str, file_dst_path_str, str(why), "copystat error"))

    #     # Fail if any errors were found
    #     if errors:
    #         raise EnvironmentError(errors)
