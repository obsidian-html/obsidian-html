import os
import yaml
import json

from pathlib import Path

from ...core.FileObject import FileObject
from ...parser.MarkdownPage import MarkdownPage

from ..base_classes import ObsidianHtmlModule


class FilterOnMetadataModule(ObsidianHtmlModule):
    """
    This module will load index/metadata.json, which contains a metadata record for each markdown file in the vault (after crude filtering).
    It will then test each file's metadata against the include_on and exclude_on rules, compiling an excluded_files list.
    The files index/files.json and index/markdown_files.json are then updated so that the items in excluded_files are removed from them.
    """

    @staticmethod
    def requires():
        return tuple(["index/markdown_files.json", "index/files.json", "index/metadata.json", "paths.json"])

    @staticmethod
    def provides():
        return tuple(
            [
                "index/files.json",
                "index/markdown_files.json",
                "excluded_files_by_metadata.json",
            ]
        )

    @staticmethod
    def alters():
        return tuple()

    def define_mod_config_defaults(self):
        self.mod_config["include_on"] = {
            "value": [],
            "description": [
                "Attributes to match on, will be applied if value != []",
                "You can currently use: {'tagged': 'tag_name'}",
                "First list is a list of lists that are ORed, so any list can give true and this will match",
                "The dict elements in the sublists are ANDed together, so every element needs to give true",
            ],
            "example_value": [
                [{"tagged": "type/automation"}],
            ],
        }
        self.mod_config["exclude_on"] = {
            "value": [],
            "description": [
                "Works the same as 'include_on', but in reverse.",
                "Include_on results in an 'excluded_files' list, as does this setting. Both lists are summed.",
            ],
            "example_value": [
                [{"tagged": "type/automation"}],
            ],
        }

    def accept(self, module_data_folder):
        """This function is run before run(), if it returns False, then the module run is skipped entirely. Any other value will be accepted"""
        return

    def test_requirement(self, element, metadata):
        if "tagged" in element.keys():
            return self.test_function_tagged(metadata, element)
        elif "present" in element.keys():
            return self.test_function_present(metadata, element)
        elif "flag" in element.keys():
            return self.test_function_flag(metadata, element)
        elif "equals" in element.keys():
            return self.test_function_equals(metadata, element)
        else:
            raise Exception(f"element {element} is not recognized as a valid selector")
        return False

    def test_function_tagged(self, metadata, element):
        """ {"tagged": "<tag_name>"} - returns true if the tag exists in metadata["tags"] """
        return element["tagged"] in metadata["tags"]

    def test_function_present(self, metadata, element):
        """ {"present": "<tag_name>"} - returns true if the key exists in metadata """
        def _test_key_exists(dictionary, key):
            # simple test
            if '/' not in key:
                return key in dictionary

            # multiple levels: test first level, then recurse
            head, tail = key.split("/", 1)
            if head not in dictionary:
                return False
            
            return _test_key_exists(dictionary[head], tail)

        return _test_key_exists(metadata, element["present"])

    def test_function_flag(self, metadata, element):
        """ {"flag": "<tag_name>"} - same as "present" but value of the key should also be true """
        def _test_key_exists(dictionary, key):
            # simple test
            if '/' not in key:
                if key in dictionary:
                    return bool(dictionary[key])
                else:
                    return False

            # multiple levels: test first level, then recurse
            head, tail = key.split("/", 1)
            if head not in dictionary:
                return False
            
            return _test_key_exists(dictionary[head], tail)
            
        return _test_key_exists(metadata, element["flag"])

    def test_function_equals(self, metadata, element):
        """ {"flag": "<tag_name>"} - same as "present" but value of the key should also be equal to the given value """
        def _test_key_has_value(dictionary, key, value):
            # simple test
            if '/' not in key:
                if key in dictionary:
                    return (value == dictionary[key])
                else:
                    return False

            # multiple levels: test first level, then recurse
            head, tail = key.split("/", 1)
            if head not in dictionary:
                return False
            
            return _test_key_has_value(dictionary[head], tail, value)
            
        return _test_key_has_value(metadata, element["equals"][0], element["equals"][1])

    def test_publish(self, rel_path, metadata, include_on):
        if len(include_on) == 0:
            return True

        for and_list in include_on:
            publish = True
            for element in and_list:
                # when ever a test fails, publish will toggle permanently to false
                publish = publish and self.test_requirement(element, metadata)

            # if one and_list is true, this means that the result is already known
            # as all and_lists are orred together, so exit early
            if publish:
                return True

        return False

    def test_exclude(self, rel_path, metadata, exclude_on):
        if len(exclude_on) == 1 and len(exclude_on[0]) == 0:
            return False

        for and_list in exclude_on:
            exclude = True
            for element in and_list:
                # when ever a test fails, exclude will toggle permanently to false
                exclude = exclude and self.test_requirement(element, metadata)

            # if one and_list is true, this means that the result is already known
            # as all and_lists are orred together, so exit early
            if exclude:
                return True

        return False

    def run(self):
        # get input
        paths = self.modfile("paths.json").read().from_json()

        md_files = self.modfile("index/markdown_files.json").read().from_json()
        metadata_dict = self.modfile("index/metadata.json").read().from_json()

        include_on = self.value_of("include_on")
        exclude_on = self.value_of("exclude_on")

        # judge each file
        exclude_list = []
        for file in md_files:
            rel_path = Path(file).relative_to(paths["input_folder"]).as_posix()
            metadata = metadata_dict[rel_path]

            # test whether include_on says to publish the file
            publish = self.test_publish(rel_path, metadata, include_on)
            if publish is False:
                exclude_list.append(file)

            # test whether exclude_on says to exclude the file
            exclude = self.test_exclude(rel_path, metadata, exclude_on)
            if exclude:
                exclude_list.append(file)

        # remove duplicates
        exclude_list = list(set(exclude_list))

        # check that the entrypoint file is not being filtered out
        if paths["entrypoint"] in exclude_list:
            self.print("ERROR", f'You have configured {self.nametag} to filter out {paths["entrypoint"]}, which is your entrypoint. Correct this and run again.')
            exit(1)

        # update file lists
        new_md_files = [x for x in md_files if x not in exclude_list]
        self.modfile("index/markdown_files.json", new_md_files).to_json().write()

        files = self.modfile("index/files.json").read().from_json()
        new_files = [x for x in files if (x not in exclude_list)]
        self.modfile("index/files.json", new_files).to_json().write()

        # record the files that were excluded
        self.modfile("excluded_files_by_metadata.json", exclude_list).to_json().write()

    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def integrate_save(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass
