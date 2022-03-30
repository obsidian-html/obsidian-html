from __future__ import annotations
from pathlib import Path
from typing import Type
import datetime
import platform
import os
import inspect
import shutil               # used to remove a non-empty directory, copy files

'''
This object class helps us with keeping track of all the paths.
There are three types of paths:

- obsidian notes: 'notes'
- proper markdown notes: 'markdown'
- html pages: 'html'

The flow within ObsidianHtml is to get obsidian notes and convert them to markdown notes,
then take the proper markdown notes and convert them to html.

When we set the note path as a source, then we will know what the markdown path will be, based on the config.
And when we know the markdown path we can set the html path.

Because the first step can be skipped, there is some complexity, but otherwise, if we give the note path as a source,
we can compile all the relevant paths in one pass.

The links have some complexity because we can configure to use absolute links or relative links.
For simplicity's sake, we just compile both link types within the same function. There are some functions to automatically
get the correct link based on the configurations.
'''

class OH_File:
    pb = None                   # contains all config, paths, etc (global pass in config object)
    path = None                 # hashtable with all relevant file paths
    link = None                 # hashtable with all links
    metadata = None             # information on the note, such as modified_date

    processed_ntm = False       # whether the note has already been processed in the note --> markdown flow
    processed_mth = False       # whether the note has already been processed in the markdown --> html flow

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

    def init_note_path(self, source_file_absolute_path, compile_metadata=True):
        self.oh_file_type = 'obs_to_md'

        # Configured folders
        source_folder_path = self.pb.paths['obsidian_folder']
        target_folder_path = self.pb.paths['md_folder']

        # Note
        self.path['note'] = {}
        self.path['note']['folder_path'] = source_folder_path
        self.path['note']['file_absolute_path'] = source_file_absolute_path
        self.path['note']['file_relative_path'] = source_file_absolute_path.relative_to(source_folder_path)
        self.path['note']['suffix'] = self.path['note']['file_absolute_path'].suffix[1:]

        # Markdown
        self.path['markdown'] = {}
        self.path['markdown']['folder_path'] = target_folder_path

        if self.path['note']['file_relative_path'] == self.pb.paths['rel_obsidian_entrypoint']:
            # rewrite path to index.md if the note is configured as the entrypoint.
            self.metadata['is_entrypoint'] = True
            self.path['markdown']['file_absolute_path'] = target_folder_path.joinpath('index.md')
            self.path['markdown']['file_relative_path'] = self.path['markdown']['file_absolute_path'].relative_to(target_folder_path)

            # also add self to pb.files under the key 'index.md' so it is findable
            self.pb.files['index.md'] = self
        else:
            self.path['markdown']['file_absolute_path'] = target_folder_path.joinpath(self.path['note']['file_relative_path'])
            self.path['markdown']['file_relative_path'] = self.path['note']['file_relative_path']

        self.path['markdown']['suffix'] = self.path['markdown']['file_absolute_path'].suffix[1:]

        # Metadata
        self.metadata['depth'] = self._get_depth(self.path['note']['file_relative_path'])
        if compile_metadata:
            self.compile_metadata(source_file_absolute_path)            # is_note, creation_time, modified_time, is_video, is_audio, is_includable

    def init_markdown_path(self, source_file_absolute_path=None):
        self.oh_file_type = 'md_to_html'

        source_folder_path = self.pb.paths['md_folder']
        target_folder_path = self.pb.paths['html_output_folder']

        # compile the path['markdown'] section, or reuse the section from the previous step
        if source_file_absolute_path is None:
            source_file_absolute_path = self.path['markdown']['file_absolute_path']
        else:
            self.path['markdown'] = {}
            self.path['markdown']['folder_path'] = source_folder_path
            self.path['markdown']['file_absolute_path'] = source_file_absolute_path
            self.path['markdown']['file_relative_path'] = source_file_absolute_path.relative_to(source_folder_path)
            self.path['markdown']['suffix'] = source_file_absolute_path.suffix[1:]

        # html
        self.path['html'] = {}
        self.path['html']['folder_path'] = target_folder_path

        if self.path['markdown']['file_relative_path'] == self.pb.paths['rel_md_entrypoint_path']:
            # rewrite path to index.html if the markdown note is configured as the entrypoint.
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

        # Metadata
        # call to self.compile_metadata() should be done manually in the calling function
        self.metadata['depth'] = self._get_depth(self.path['html']['file_relative_path'])

    def compile_metadata(self, path, cached=False):
        if cached and 'is_note' in self.metadata:
            return
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

    def get_link(self, link_type, origin:'OH_File'=None, origin_rel_dst_path_str=None):
        # Get origin_rel_dst_path_str
        if origin_rel_dst_path_str is None:
            if origin is not None:
                origin_rel_dst_path_str = origin.path[link_type]['file_relative_path'].as_posix()
            else:
                origin_rel_dst_path_str = self.path[link_type]['file_relative_path'].as_posix()

        # recompile links for the given origin_path and return correct link (absolute or relative)
        if link_type == 'markdown':
            self.compile_markdown_link(origin_rel_dst_path_str)

            if self.pb.gc('toggles/relative_path_md', cached=True):
                return self.link[link_type]['relative']

        elif link_type == 'html':
            self.compile_html_link(origin_rel_dst_path_str)

            if self.pb.gc('toggles/relative_path_html', cached=True):
                return self.link[link_type]['relative']

        return self.link[link_type]['absolute']

    def compile_markdown_link(self, origin_rel_dst_path_str):
        self.link['markdown'] = {}

        # Absolute
        web_abs_path = self.path['markdown']['file_relative_path'].as_posix()
        self.link['markdown']['absolute'] = '/'+web_abs_path

        # Relative
        prefix = get_rel_html_url_prefix(origin_rel_dst_path_str)
        self.link['markdown']['relative'] = prefix+'/'+web_abs_path

    def compile_html_link(self, origin_rel_dst_path_str):
        self.link['html'] = {}

        # Absolute
        html_url_prefix = self.pb.gc('html_url_prefix')
        abs_link = self.path['html']['file_relative_path'].as_posix()
        self.link['html']['absolute'] = html_url_prefix+'/'+abs_link

        # Relative
        prefix = get_rel_html_url_prefix(origin_rel_dst_path_str)
        self.link['html']['relative'] = prefix+'/'+self.path['html']['file_relative_path'].as_posix()

    def copy_file(self, mode):
        if mode == 'ntm':
            src_file_path = self.path['note']['file_absolute_path']
            dst_file_path = self.path['markdown']['file_absolute_path']
        elif mode == 'mth':
            src_file_path = self.path['markdown']['file_absolute_path']
            dst_file_path = self.path['html']['file_absolute_path']

        dst_file_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src_file_path, dst_file_path)

def get_rel_html_url_prefix(rel_path):
    depth = rel_path.count('/')
    if depth > 0:
        prefix = ('../'*depth)[:-1]
    else:
        prefix = '.'
    return prefix

def get_html_url_prefix(pb, rel_path_str=None, abs_path_str=None):
    # check input and convert rel_path_str from abs_path_str if necessary
    if rel_path_str is None:
        if abs_path_str is None:
            raise Exception("pass in either rel_path_str or abs_path_str")
        rel_path_str = Path(abs_path_str).relative_to(pb.paths['html_output_folder']).as_posix()

    # return html_prefix
    if pb.gc('toggles/relative_path_html', cached=True):
        html_url_prefix = pb.sc(path='html_url_prefix', value=get_rel_html_url_prefix(rel_path_str))
    else:
        html_url_prefix = pb.gc('html_url_prefix')
    return html_url_prefix