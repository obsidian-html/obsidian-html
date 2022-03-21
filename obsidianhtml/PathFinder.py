from __future__ import annotations
from pathlib import Path
from typing import Type
import datetime
import platform
import os
import inspect
import shutil               # used to remove a non-empty directory, copy files

class OH_File:
    pb = None
    path = None
    link = None
    metadata = None

    oh_file_type = None

    processed_ntm = False
    processed_mth = False

    def __init__(self, pb):
        self.pb = pb 

        self.path = {}
        self.link = {}
        self.metadata = {}

        # These values are not set under self.compile_metadata()
        # So the default values need to be set here.
        self.metadata['is_entrypoint'] = False

    def fullpath(self, output):
        return self.path[output]['file_absolute_path']

    def is_valid_note(self, output):
        if self.fullpath(output).exists() == False:
            return False
        if self.fullpath(output).suffix != '.md':
            return False

        return True

    def init_note_path(self, source_file_absolute_path, source_folder_path=None, target_folder_path=None, compile_metadata=True):
        self.oh_file_type = 'obs_to_md'

        # File paths
        if source_folder_path is None:
            source_folder_path = self.pb.paths['obsidian_folder']
        if target_folder_path is None:
            target_folder_path = self.pb.paths['md_folder']

        self.path['note'] = {}
        self.path['note']['folder_path'] = source_folder_path
        self.path['note']['file_absolute_path'] = source_file_absolute_path
        self.path['note']['file_relative_path'] = source_file_absolute_path.relative_to(source_folder_path)
        self.path['note']['suffix'] = self.path['note']['file_absolute_path'].suffix[1:]

        self.path['markdown'] = {}
        self.path['markdown']['folder_path'] = target_folder_path

        if self.path['note']['file_relative_path'] == self.pb.paths['rel_obsidian_entrypoint']:
            self.metadata['is_entrypoint'] = True
            self.path['markdown']['file_absolute_path'] = target_folder_path.joinpath('index.md')
            self.path['markdown']['file_relative_path'] = self.path['markdown']['file_absolute_path'].relative_to(target_folder_path)
            self.pb.files['index.md'] = self
        else:
            self.path['markdown']['file_absolute_path'] = target_folder_path.joinpath(self.path['note']['file_relative_path'])
            self.path['markdown']['file_relative_path'] = self.path['note']['file_relative_path']

        self.path['markdown']['suffix'] = self.path['markdown']['file_absolute_path'].suffix[1:]

        # Metadata
        self.metadata['depth'] = self._get_depth(self.path['note']['file_relative_path'])

        # is_note, creation_time, modified_time, is_video, is_audio, is_includable
        if compile_metadata:
            self.compile_metadata(source_file_absolute_path)

    def init_markdown_path(self, source_file_absolute_path=None, source_folder_path=None, target_folder_path=None):
        self.oh_file_type = 'md_to_html'

        if source_folder_path is None:
            source_folder_path = self.pb.paths['md_folder']
        if target_folder_path is None:
            target_folder_path = self.pb.paths['html_output_folder']

        if source_file_absolute_path is None:
            source_file_absolute_path = self.path['markdown']['file_absolute_path']
        else:
            self.path['markdown'] = {}
            self.path['markdown']['folder_path'] = source_folder_path
            self.path['markdown']['file_absolute_path'] = source_file_absolute_path
            self.path['markdown']['file_relative_path'] = source_file_absolute_path.relative_to(source_folder_path)
            self.path['markdown']['suffix'] = source_file_absolute_path.suffix[1:]

        
        self.path['html'] = {}
        self.path['html']['folder_path'] = target_folder_path

        if self.path['markdown']['file_relative_path'] == self.pb.paths['rel_md_entrypoint_path']:
            self.metadata['is_entrypoint'] = True
            self.path['html']['file_absolute_path'] = target_folder_path.joinpath('index.html')
            self.path['html']['file_relative_path'] = self.path['html']['file_absolute_path'].relative_to(target_folder_path)
        else:
            # rewrite markdown suffix to html suffix
            target_rel_path_posix = self.path['markdown']['file_relative_path'].as_posix()
            if target_rel_path_posix[-3:] == '.md':
                target_rel_path = Path(target_rel_path_posix[:-3] + '.html')
            else:
                target_rel_path = Path(target_rel_path_posix)

            self.path['html']['file_absolute_path'] = target_folder_path.joinpath(target_rel_path)
            self.path['html']['file_relative_path'] = target_rel_path
            self.path['html']['suffix'] = self.path['html']['file_absolute_path'].suffix[1:]

        self.metadata['depth'] = self._get_depth(self.path['html']['file_relative_path'])

    def compile_metadata(self, path):
        self.set_times(path)
        self.set_file_types(path)

    def set_file_types(self, path):
        self.metadata['is_note'] = False
        self.metadata['is_video'] = False
        self.metadata['is_audio'] = False
        self.metadata['is_includable_file'] = False
        self.metadata['is_parsable_note'] = False

        suffix = path.suffix[1:]
        
        if suffix == 'md':
            self.metadata['is_note'] = True
        if suffix in self.pb.gc('included_file_suffixes', cached=True):
            self.metadata['is_includable_file'] = True
        if suffix in self.pb.gc('video_format_suffixes', cached=True):
            self.metadata['is_video'] = True
        if suffix in self.pb.gc('audio_format_suffixes', cached=True):
            self.metadata['is_audio'] = True

        if path.exists() and self.metadata['is_note']:
            self.metadata['is_parsable_note'] = True

    def set_times(self, path):
        if platform.system() == 'Windows' or platform.system() == 'Darwin':
            self.metadata['creation_time'] = datetime.datetime.fromtimestamp(os.path.getctime(path)).isoformat()
            self.metadata['modified_time'] = datetime.datetime.fromtimestamp(os.path.getmtime(path)).isoformat()
        else:
            self.metadata['modified_time'] = datetime.datetime.fromtimestamp(os.path.getmtime(path)).isoformat()

    def get_depth(self, mode):
        return self._get_depth(self.path[mode]['file_relative_path'])
    def _get_depth(self, rel_path):
        return rel_path.as_posix().count('/')

    def compile_link(self, origin:'OH_File'=None):
        if self.oh_file_type == 'obs_to_md':
            self.compile_markdown_link(origin)
        elif self.oh_file_type == 'md_to_html':
            self.compile_html_link(origin)

    def get_link(self, link_type, origin:'OH_File'=None):
        # print(inspect.stack()[1][3])
        # print('target', self.path['note']['file_relative_path'], self.metadata['depth'])
        # if origin is not None:
        #     print('origin', origin.path['note']['file_relative_path'], origin.metadata['depth'])
        # else:
        #     print('origin', 'none')

        # recompile links if not compiled yet
        if link_type == 'markdown':
            self.compile_markdown_link(origin)

            if self.pb.gc('toggles/relative_path_md', cached=True):
                return self.link[link_type]['relative']

        elif link_type == 'html':
            self.compile_html_link(origin)

            if self.pb.gc('toggles/relative_path_html', cached=True):
                return self.link[link_type]['relative']

        return self.link[link_type]['absolute']

    def compile_markdown_link(self, origin:'OH_File'=None):
        self.link['markdown'] = {}

        # Absolute
        web_abs_path = self.path['markdown']['file_relative_path'].as_posix()
        self.link['markdown']['absolute'] = '/'+web_abs_path

        # Relative
        if origin is None:
            pd = self.metadata['depth']
        else:
            pd = origin.metadata['depth']
        self.link['markdown']['relative'] = (pd*'../')+web_abs_path

    def compile_html_link(self, origin:'OH_File'=None):
        self.link['html'] = {}

        # Absolute
        html_url_prefix = self.pb.gc('html_url_prefix')
        abs_link = self.path['html']['file_relative_path'].as_posix()
        if abs_link[0] != '/':
            abs_link = html_url_prefix+'/'+abs_link
        self.link['html']['absolute'] = abs_link

        # Relative
        if origin is None:
            pd = self.metadata['depth']
        else:
            pd = origin.metadata['depth']
        self.link['html']['relative'] = (pd*'../')+self.path['html']['file_relative_path'].as_posix()

        if self.link['html']['relative'][0] != '.':
            self.link['html']['relative'] = './' + self.link['html']['relative']

    def copy_file(self, mode):
        if mode == 'ntm':
            src_file_path = self.path['note']['file_absolute_path']
            dst_file_path = self.path['markdown']['file_absolute_path']
        elif mode == 'mth':
            src_file_path = self.path['markdown']['file_absolute_path']
            dst_file_path = self.path['html']['file_absolute_path']

        dst_file_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src_file_path, dst_file_path)
