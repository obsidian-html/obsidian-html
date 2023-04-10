from ..base_classes import ObsidianHtmlModule

# from ...lib import FindVaultByEntrypoint

import yaml
from pathlib import Path


class HtmlTemplaterModule(ObsidianHtmlModule):
    """
    - Loads the template to be used for generating the html pages. This can be a built-in template or a user provided one.
      (The run method)
      It is also used to create the html pages (the populate_template method).
    - Defaults to persistent mode, but can also be used with persistence off. The latter will mean that the template will be loaded from
      disk for every note.
    """

    @property
    def requires(self):
        return tuple(["config.yml"])

    @property
    def provides(self):
        return tuple(["template.html"])

    @property
    def alters(self):
        return tuple()

    def run(self):
        if hasattr(self, "memory"):
            print("Hi, I am back")
        else:
            print("Hi, who are you")
            self.memory = True

        # Default to persistent mode
        if self.persistent is not True:
            print("Warning, I should be run with persistence = True!")

        gc = self.gc

        # paths = {
        #     "obsidian_folder": Path(self.set_obsidian_folder_path_str()),
        #     "md_folder": Path(gc("md_folder_path_str")).resolve(),
        #     "obsidian_entrypoint": Path(gc("obsidian_entrypoint_path_str")).resolve(),
        #     "md_entrypoint": Path(gc("md_entrypoint_path_str")).resolve(),
        #     "html_output_folder": Path(gc("html_output_folder_path_str")).resolve(),
        # }
        # paths["original_obsidian_folder"] = paths["obsidian_folder"]  # use only for lookups!
        # paths["dataview_export_folder"] = paths["obsidian_folder"].joinpath(gc("toggles/features/dataview/folder"))

        # if gc("toggles/extended_logging", cached=True):
        #     paths["log_output_folder"] = Path(gc("log_output_folder_path_str")).resolve()

        # # Deduce relative paths
        # if gc("toggles/compile_md", cached=True):
        #     paths["rel_obsidian_entrypoint"] = paths["obsidian_entrypoint"].relative_to(paths["obsidian_folder"])
        # paths["rel_md_entrypoint_path"] = paths["md_entrypoint"].relative_to(paths["md_folder"])

        # # Convert to posix string for exporting
        # for key in paths.keys():
        #     paths[key] = paths[key].as_posix()

        # # Export
        # self.modfile("paths.json", paths).to_json().write()

    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def integrate_save(self, pb):
        #     """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    #     pb.paths = self.modfile("paths.json").read().from_json().unwrap()
    #     for key in pb.paths:
    #         pb.paths[key] = Path(pb.paths[key])
