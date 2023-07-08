import yaml

from pathlib import Path
from appdirs import AppDirs

from ..base_classes import ObsidianHtmlModule
from ...lib import find_vault_folder_by_entrypoint


class LoadPathsModule(ObsidianHtmlModule):
    """
    Based on the config.yml we can determine paths of relevance, such as the html output folder. These paths will be put in paths.yml
    Paths are all encoded as posix strings. Paths are absolute unless prefixed with _rel
    """

    @staticmethod
    def requires():
        return tuple(["config.yml"])

    @staticmethod
    def provides():
        return tuple(["paths.json"])

    @staticmethod
    def alters():
        return tuple()

    # REFACTOR
    def set_obsidian_folder_path_str(self):
        if self.gc("toggles/compile_md") is False:  # don't check vault if we are compiling directly from markdown to html
            return ""

        # Use user provided obsidian_folder_path_str
        if "obsidian_folder_path_str" in self.config and self.config["obsidian_folder_path_str"] not in ["", "<DEPRECATED>"]:
            result = find_vault_folder_by_entrypoint(self.config["obsidian_folder_path_str"])
            # check that entrypoint is located inside an obsidian vault
            if result:
                if Path(result) != Path(self.config["obsidian_folder_path_str"]).resolve():
                    print(f"Error: The configured obsidian_folder_path_str is not the vault root. Change its value to {result}")
                    exit(1)
                return self.check_entrypoint_exists(result)
            else:
                print("ERROR: Obsidianhtml could not find a valid vault. (Tip: obsidianhtml looks for the .obsidian folder)")
                exit(1)
            return self.check_entrypoint_exists(result)

        # Determine obsidian_folder_path_str from obsidian_entrypoint_path_str
        result = find_vault_folder_by_entrypoint(self.config["obsidian_entrypoint_path_str"])
        if result:
            return self.check_entrypoint_exists(result)
        else:
            print(
                f"ERROR: Obsidian vault not found based on entrypoint {self.config['obsidian_entrypoint_path_str']}.\n\tDid you provide a note that is in a valid vault? (Tip: obsidianhtml looks for the .obsidian folder)"
            )
            exit(1)

    def check_entrypoint_exists(self, entrypoint):
        """Returns the inputted entrypoint, if the file exists, otherwise it errors"""
        if self.config["toggles"]["compile_md"] is False:  # don't check vault if we are compiling directly from markdown to html
            return entrypoint
        if not Path(entrypoint).exists():
            print(f"Error: entrypoint note {self.config['obsidian_entrypoint_path_str']} does not exist.")
            exit(1)
        return entrypoint

    def accept(self, module_data_folder):
        """This function is run before run(), if it returns False, then the module run is skipped entirely. Any other value will be accepted"""
        return

    def run(self):
        gc = self.gc

        paths = {
            "obsidian_folder": Path(self.set_obsidian_folder_path_str()),
            "md_folder": Path(gc("md_folder_path_str")).resolve(),
            "obsidian_entrypoint": Path(gc("obsidian_entrypoint_path_str")).resolve(),
            "md_entrypoint": Path(gc("md_entrypoint_path_str")).resolve(),
            "html_output_folder": Path(gc("html_output_folder_path_str")).resolve(),
            "appdir": Path(AppDirs("obsidianhtml", "obsidianhtml").user_config_dir),
        }
        paths["original_obsidian_folder"] = paths["obsidian_folder"]  # use only for lookups!
        paths["original_obsidian_entrypoint"] = paths["obsidian_entrypoint"]  # use only for lookups!
        paths["dataview_export_folder"] = paths["obsidian_folder"].joinpath(gc("toggles/features/dataview/folder"))

        # Deduce relative paths
        if gc("toggles/compile_md", cached=True):
            paths["rel_obsidian_entrypoint"] = paths["obsidian_entrypoint"].relative_to(paths["obsidian_folder"])
        paths["rel_md_entrypoint_path"] = paths["md_entrypoint"].relative_to(paths["md_folder"])

        # set input folder / entrypoint
        if gc("toggles/compile_md"):
            paths["input_folder"] = paths["obsidian_folder"]
            paths["entrypoint"] = paths["obsidian_entrypoint"]
        else:
            paths["input_folder"] = paths["md_folder"]
            paths["entrypoint"] = paths["md_entrypoint"]

        paths["original_input_folder"] = paths["input_folder"]

        # Convert to posix string for exporting
        for key in paths.keys():
            paths[key] = paths[key].as_posix()

        # Export
        self.modfile("paths.json", paths).to_json().write()

    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def integrate_save(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pb.paths = self.modfile("paths.json").read().from_json().unwrap()
        for key in pb.paths:
            pb.paths[key] = Path(pb.paths[key])
