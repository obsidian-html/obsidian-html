from .. import ObsidianHtmlModule

import sys


class ParseSysArgsModule(ObsidianHtmlModule):
    """
    This module will create the arguments.yml file based on the given sysargs.
    """

    @property
    def requires(self):
        return tuple()

    @property
    def provides(self):
        return tuple(["arguments.yml"])

    @property
    def alters(self):
        return tuple()

    def determine_command(self):
        if "-h" in sys.argv or "--help" in sys.argv or "help" in sys.argv:
            return "help"

        if len(sys.argv) < 2 or sys.argv[1][0] == "-":
            self.print("deprecation", 'DEPRECATION WARNING: You did not pass in a command. Assuming you meant "convert". Starting version 4.0.0 providing a command will become mandatory.')
            return "convert"
        else:
            command = sys.argv[1]

    def determine_config_path(self):
        for i, v in enumerate(sys.argv):
            if v == "-i":
                if len(sys.argv) < (i + 2):
                    self.print("error", "No config path given.\n  Use `obsidianhtml convert -i /target/path/to/config.yml` to provide input.")
                    exit(1)
                return sys.argv[i + 1]
        return ""

    def run(self):
        self.print("info", f"running {self.module_name}")

        arguments = {}
        arguments["command"] = self.determine_command()
        arguments["config_path"] = self.determine_config_path()

        self.write("arguments.yml", arguments, asyaml=True)
