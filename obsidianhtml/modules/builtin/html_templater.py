import yaml
from pathlib import Path

from ..base_classes import ObsidianHtmlModule
from ...lib import OpenIncludedFile


class HtmlTemplaterModule(ObsidianHtmlModule):
    """
    - Loads the template to be used for generating the html pages. This can be a built-in template or a user provided one.
      (The run method)
      It is also used to create the html pages (the populate_template method).
    - Defaults to persistent mode, but can also be used with persistence off. The latter will mean that the template will be loaded from
      disk for every note.
    """

    @staticmethod
    def requires():
        return tuple(["config.yml"])

    @staticmethod
    def provides():
        return tuple(
            [
                "html/note.template.html",
                "html/dynamic_inclusions.html",
                "html/dynamic_footer_inclusions.html",
            ]
        )

    @staticmethod
    def alters():
        return tuple()

    def accept(self, module_data_folder):
        """This function is run before run(), if it returns False, then the module run is skipped entirely. Any other value will be accepted"""
        return

    def run(self):
        self.get_html_template()
        self.compile_dynamic_inclusions()

    def get_html_template(self):
        gc = self.gc

        # write empty file that we promised to provide and exit, if html is not compiled
        if gc("toggles/compile_html") == False:
            self.modfile("html/note.template.html", "").write()
            return

        html_template = ""
        try:
            with open(Path(gc("html_template_path_str")).resolve()) as f:
                html_template = f.read()
        except:
            layout = gc("toggles/features/styling/layout")
            html_template = OpenIncludedFile(f"html/layouts/template_{layout}.html")

        if "{content}" not in html_template:
            raise Exception("The provided html template does not contain the string `{content}`. This will break its intended use as a template.")
            return False

        self.modfile("html/note.template.html", html_template).write()
        self.store("html_template", html_template)

    def compile_dynamic_inclusions(self):
        # This is a set of javascript/css files to be loaded into the header based on config choices.
        dynamic_inclusions = ""
        try:
            dynamic_inclusions += "\n".join(self.gc("html_custom_inclusions")) + "\n"
        except:
            pass

        self.store("dynamic_inclusions", dynamic_inclusions)
        self.modfile("html/dynamic_inclusions.html", dynamic_inclusions).write()

        # This is a set of javascript/css files to be loaded into the footer based on config choices.
        dynamic_footer_inclusions = ""
        try:
            dynamic_footer_inclusions += "\n".join(self.gc("html_custom_footer_inclusions")) + "\n"
        except:
            pass

        self.store("dynamic_footer_inclusions", dynamic_footer_inclusions)
        self.modfile("html/dynamic_footer_inclusions.html", dynamic_footer_inclusions).write()

    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def integrate_save(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pb.html_template = self.retrieve("html_template")
        pb.dynamic_inclusions = self.retrieve("dynamic_inclusions")
        pb.dynamic_footer_inclusions = self.retrieve("dynamic_footer_inclusions")
