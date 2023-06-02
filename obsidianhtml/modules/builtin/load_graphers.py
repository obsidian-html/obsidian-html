import yaml
from pathlib import Path

from ..base_classes import ObsidianHtmlModule
from ...lib import OpenIncludedFile


class LoadGrapherModule(ObsidianHtmlModule):
    """
    To be refactored. It's not nice how the html template and graph template are now dependent on eachother.
    """

    @staticmethod
    def requires():
        return tuple(["config.yml"])

    @staticmethod
    def provides():
        return tuple(
            [
                "html/graph.template.html",
                "html/graph_full_page.template.html",
                "graphers.json",
            ]
        )

    @staticmethod
    def alters():
        return tuple()

    def accept(self, module_data_folder):
        """This function is run before run(), if it returns False, then the module run is skipped entirely. Any other value will be accepted"""
        return

    def run(self):
        gc = self.gc

        # write empty files that we promised to provide and exit
        if gc("toggles/compile_html") == False:
            self.modfile("html/graph.template.html", "").write()
            self.modfile("html/graph_full_page.template.html", "").write()
            self.modfile("graphers.json", "[{}]").write()
            return

        # Get graph templates
        graph_template = OpenIncludedFile("graph/graph_template.html")
        self.store("graph_template", graph_template)
        self.modfile("html/graph.template.html", graph_template).write()

        graph_full_page_template = OpenIncludedFile("graph/graph_full_page.html")
        self.store("graph_full_page_template", graph_full_page_template)
        self.modfile("html/graph_full_page.template.html", graph_full_page_template).write()

        # Get grapher template code
        graphers = []
        for grapher in gc("toggles/features/graph/templates"):
            gid = grapher["id"]

            # get contents of the file
            if grapher["path"].startswith("builtin<"):
                grapher["contents"] = OpenIncludedFile(f"graph/default_grapher_{gid}.js")
            else:
                try:
                    with open(Path(grapher["path"]).resolve()) as f:
                        grapher["contents"] = f.read()
                except:
                    raise Exception(f"Could not open user provided grapher file with path {grapher['path']}")

            graphers.append(grapher)

        self.modfile("graphers.json", graphers).to_json().write()
        self.store("graphers", graphers)

    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def integrate_save(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pb.graph_template = self.retrieve("graph_template")
        pb.graph_full_page_template = self.retrieve("graph_full_page_template")

        # pb.graphers = self.retrieve("graphers")
        pb.graphers = self.modfile("graphers.json").read().from_json()  # read from file to test json conversion issues
