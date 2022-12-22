import os
import shutil
import glob
import tempfile             # used to create temporary files/folders

from subprocess import Popen, PIPE
from pathlib import Path

from ..core import Types as T
from ..lib import is_installed, pushd, should_ignore


def CreateTemporaryCopy(source_folder_path, pb):
    # Create temp dir
    tmpdir = tempfile.TemporaryDirectory()

    print(f"> COPYING VAULT {source_folder_path} TO {tmpdir.name}")

    if pb.gc('toggles/verbose_printout'):
        print('\tWill overwrite paths: obsidian_folder, obsidian_entrypoint')

    # Decide which method to use
    copy_method = pb.gc('copy_vault_to_tempdir_method')

    if copy_method == 'default':
        if is_installed('rsync'):
            copy_method = 'rsync'
        else:
            copy_method = 'shutil'

    if pb.gc('copy_vault_to_tempdir_method') == 'rsync':
        if is_installed('rsync'):
            copy_method = 'rsync'
        else:
            print('WARNING: copy_vault_to_tempdir_method was set to rsync, but rsync is not present on the system. Defaulting to shutil copy method.')
            copy_method = 'shutil'

    # Call copytree function (rsync)
    if copy_method == 'rsync':
        copy_tree_rsync(source_folder_path.as_posix(), tmpdir.name, exclude=pb.gc('exclude_glob'), verbose=pb.gc('copy_vault_to_tempdir_follow_copy'))

    # Fetch invalid settings
    elif copy_method not in ['shutil', 'shutil_walk']:
        raise Exception(f"Copy method of {copy_method} not known.")
    else:
        # Compile ignore list
        excluded_paths = []
        if isinstance(pb.gc('exclude_glob', cached=True), list):
            owd = pushd(source_folder_path)          # move working dir to root dir (needed for glob)
            for line in pb.gc('exclude_glob', cached=True):
                excluded_paths += glob.glob(line, recursive=True)
            excluded_paths = [Path(x) for x in excluded_paths]
            print('Paths that will be ignored:', [x.as_posix() for x in excluded_paths])
            os.chdir(owd)

        # Call copytree function (shutil_walk or shutil)
        if pb.gc('copy_vault_to_tempdir_method') == 'shutil_walk':
            copytree_shutil_walk(source_folder_path, tmpdir.name, ignore=excluded_paths, pb=pb)
        else:
            copytree_shutil(source_folder_path, tmpdir.name, ignore=excluded_paths, pb=pb)

    print("< COPYING VAULT: Done")
    return tmpdir

def copy_tree_rsync(src_dir, dst_dir, exclude, verbose=False):
    # Get relative ignore paths
    exclude_list = []
    for path in exclude:
        exclude_list += ['--exclude', path]

    # compile command
    if src_dir[-1] != '/':
        src_dir += '/'
    if dst_dir[-1] == '/':
        dst_dir = dst_dir[:-1]

    if verbose:
        settings = '-av'
    else:
        settings = '-a'

    command = ['rsync', settings, src_dir, dst_dir] + exclude_list

    print('running: \n\t', ' '.join(command))

    # run command
    p = Popen(command, stdout=PIPE, stderr=PIPE)
    output, error = p.communicate()
    if p.returncode != 0: 
        print("Copy failed %d %s %s" % (p.returncode, output.decode('ascii').replace('\\n', '\n'), error))
    else:
        print("Copy succeeded %d %s %s" % (p.returncode, output.decode('ascii').replace('\\n', '\n'), error))

def copytree_shutil(src, dst, symlinks=False, ignore=None, copy_function=shutil.copy,
             ignore_dangling_symlinks=False, pb=None):

    follow_copy = pb.gc('copy_vault_to_tempdir_follow_copy')

    names = os.listdir(src)
    # if ignore is not None:
    #     ignored_names = ignore(src, names)
    # else:
    #     ignored_names = set()

    os.makedirs(dst, exist_ok=True)
    errors = []

    for name in names:
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)

        if should_ignore(ignore, Path(srcname)):
            continue

        if follow_copy:
            print('copy: ', srcname)
        try:
            if os.path.islink(srcname):
                linkto = os.readlink(srcname)
                if symlinks:
                    os.symlink(linkto, dstname)
                else:
                    # ignore dangling symlink if the flag is on
                    if not os.path.exists(linkto) and ignore_dangling_symlinks:
                        continue
                    # otherwise let the copy occurs. copy2 will raise an error
                    copy_function(srcname, dstname)
            elif os.path.isdir(srcname):
                copytree_shutil(srcname, dstname, symlinks, ignore, copy_function, pb=pb)
            else:
                # Will raise a SpecialFileError for unsupported file types
                copy_function(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error as err:
            print(err)
            errors.extend(err.args[0])
        except EnvironmentError as why:
            errors.append((srcname, dstname, str(why), 'copyfile error'))
    try:
        shutil.copystat(src, dst)
    except OSError as why:
        if WindowsError is not None and isinstance(why, WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.extend((src, dst, str(why), 'copystat error'))
    if errors:
        raise Error(errors)

def copytree_shutil_walk(src, dst, symlinks=False, ignore=None, copy_function=shutil.copy,
             ignore_dangling_symlinks=False, pb=None):

    follow_copy = pb.gc('copy_vault_to_tempdir_follow_copy')

    errors = []

    for root, dirs, files in os.walk(src, topdown=True):
        for name in files:
            # Set paths
            file_src_path = Path(os.path.join(root, name)).resolve()
            file_dst_path = Path(dst).resolve().joinpath(file_src_path.relative_to(pb.paths['obsidian_folder']))
            file_dst_folder_path = file_dst_path.parent

            # Ignore if file is excluded or in an excluded folder (see exclude_subfolders)
            if should_ignore(ignore, file_src_path):
                continue
        
            # Get strings of path objects
            file_src_path_str = file_src_path.as_posix()
            file_dst_path_str = file_dst_path.as_posix()
            file_dst_folder_path_str = file_dst_folder_path.as_posix()

            # Create folder if it does not exist
            os.makedirs(file_dst_folder_path_str, exist_ok=True)
 
            # Copy file over
            if follow_copy:
                print('copy: ', file_src_path_str)
            try:
                if file_src_path.is_symlink(): 
                    linkto = file_src_path.readlink()
                    if symlinks:
                        os.symlink(linkto, file_dst_path_str)
                    else:
                        # ignore dangling symlink if the flag is on
                        if not os.path.exists(linkto) and ignore_dangling_symlinks:
                            continue
                        # otherwise let the copy occurs. copy2 will raise an error
                        copy_function(file_src_path_str, file_dst_folder_path_str)
                else:
                    # Will raise a SpecialFileError for unsupported file types
                    copy_function(file_src_path_str, file_dst_folder_path_str)

            # catch the Error from the recursive copytree so that we can
            # continue with other files
            except Error as err:
                print(err)
                errors.extend(err.args[0])
            except EnvironmentError as why:
                errors.append((file_src_path_str, file_dst_path_str, str(why), 'copyfile error'))
    
    # Set correct permissions on target folder
    try:
        shutil.copystat(src, dst)
    except OSError as why:
        if WindowsError is not None and isinstance(why, WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.extend((file_src_path_str, file_dst_path_str, str(why), 'copystat error'))

    # Fail if any errors were found
    if errors:
        raise EnvironmentError(errors)
