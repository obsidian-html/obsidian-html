import json
from datetime import datetime

from ..base_classes import ObsidianHtmlModule
from ..lib import format_logrule


class ResourceLoggerMetaModule(ObsidianHtmlModule):
    """
    This module keeps track of the resource states, and logs them to `log.resources`
    """

    @staticmethod
    def requires():
        return tuple(["config.yml"])

    @staticmethod
    def provides():
        return tuple(["log.resources"])

    @staticmethod
    def alters():
        return tuple()

    def new_resource_listing(self, state):
        return {"history": [], "state": state}

    def new_resource_history_listing(self, module_name, action, result):
        return {"datetime": datetime.now().isoformat(), "module_name": module_name, "action": action, "result": result}

    def setup(self):
        if not hasattr(self, "resources"):
            # create with the paths already created by setup_module (this module cannot run post-modules like this one)
            self.resources = {
                "arguments.yml": self.new_resource_listing(state="present"),
                "config.yml": self.new_resource_listing(state="present"),
                "user_config.yml": self.new_resource_listing(state="present"),
                "guid.txt": self.new_resource_listing(state="present"),
            }

    def accept(self, module_data_folder):
        """This function is run before run(), if it returns False, then the module run is skipped entirely. Any other value will be accepted"""
        return

    def run(self, module, run_module_result):
        # ensure self.resources exists
        self.setup()

        # don't apply this post-run on own normal run
        if module.module_class_name == self.module_class_name:
            return

        # get output from run_module_result
        output = run_module_result.get_output()

        # Update resource listing
        resource_state = "present"
        module_result = "succeeded"
        if output is not None:
            resource_state = "failed"
            module_result = "failed"

        # get resource logs
        written_files = []
        read_files = []
        if module.is_binary:
            written_files, read_files = self.get_binary_resource_logs(module)
        else:
            written_files = module.written_files.log
            read_files = module.read_files.log

        for record in written_files:
            resource_rel_path = record["resource_rel_path"]

            # create resourcelisting
            action = "alter"
            if resource_rel_path not in self.resources.keys():
                self.resources[resource_rel_path] = self.new_resource_listing(state=resource_state)
                action = "create"

            hist = self.new_resource_history_listing(module_name=module.module_name, action=action, result=module_result)
            hist["datetime"] = record["datetime"]

            self.resources[resource_rel_path]["history"].append(hist)

        for record in module.stored_keys.log:
            resource_rel_path = record["resource_rel_path"]

            # create resourcelisting
            action = "overwrite"
            if resource_rel_path not in self.resources.keys():
                self.resources[resource_rel_path] = self.new_resource_listing(state=resource_state)
                action = "store"

            hist = self.new_resource_history_listing(module_name=module.module_name, action=action, result=module_result)
            hist["datetime"] = record["datetime"]

            self.resources[resource_rel_path]["history"].append(hist)

        for record in read_files:
            resource_rel_path = record["resource_rel_path"]

            if resource_rel_path not in self.resources.keys():
                print(
                    format_logrule(
                        verbosity="ERROR",
                        source="resource_logger.run()",
                        message=(
                            f"Resource read but not yet written: {resource_rel_path} (according to history).",
                            f"This points to a bug/misconfiguration in module {module.module_name} ({module.module_class_name}).",
                            "(Or the module that writes that file has this meta module blacklisted).",
                        ),
                    )
                )
                self.resources[resource_rel_path] = self.new_resource_listing(state="error")

            hist = self.new_resource_history_listing(module_name=module.module_name, action="read", result="succeeded")
            hist["datetime"] = record["datetime"]

            self.resources[resource_rel_path]["history"].append(hist)

        for record in module.retrieved_keys.log:
            resource_rel_path = record["resource_rel_path"]

            if resource_rel_path not in self.resources.keys():
                print(
                    format_logrule(
                        verbosity="ERROR",
                        source="resource_logger.run()",
                        message=(
                            f"Resource retrieved but not yet written: {resource_rel_path} (according to history).",
                            f"This points to a bug/misconfiguration in module {module.module_name} ({module.module_class_name}).",
                            "(Or the module that writes that file has this meta module blacklisted).",
                        ),
                    )
                )
                self.resources[resource_rel_path] = self.new_resource_listing(state="error")

            hist = self.new_resource_history_listing(module_name=module.module_name, action="retrieve", result="succeeded")
            hist["datetime"] = record["datetime"]

            self.resources[resource_rel_path]["history"].append(hist)

    def finalize(self):
        self.setup()

        verb = {
            "alter": "altered",
            "create": "created",
            "read": "read",
            "store": "stored",
            "overwrite": "overwritten",
            "retrieve": "retrieved",
        }
        output = []
        output.append("Resource log:\n-------------")
        output.append("(arguments.yml, config.yml, and user_config.yml created by setup module)\n")

        # merge all history listings together, so that we can sort on time for chronological order
        all_hist = []
        for resource_path in self.resources.keys():
            for hist in self.resources[resource_path]["history"]:
                hist["resource_path"] = resource_path
                all_hist.append(hist)

        # sort
        all_hist_sorted = sorted(all_hist, key=lambda d: d["datetime"])  # , reverse=True)

        # compile log
        for hist in all_hist_sorted:
            if hist["action"] == "failed":
                output.append(f"[{hist['datetime']}] {hist['module_name']:20} failed;    {hist['resource_path']} [state=FAILED]")
            else:
                output.append(f"[{hist['datetime']}] {hist['module_name']:20} {verb[hist['action']]:10} {hist['resource_path']:20}")

        # write to resource
        output.append("\n(log.resources created by resource_logger module)")
        self.modfile("log.resources", contents="\n".join(output)).write()

        if self.verbose_enough("debug", self.verbosity):
            output = ["writing to `log.resources`:\n"] + output + [""]
            self.print("DEBUG", "\n".join(output), force=True)

    def get_binary_resource_logs(self, module):
        ral_modfile = self.modfile(f"instances/resources_access/{module.instance_id}.csv")
        contents = ral_modfile.read(sneak=True).text()

        write_log = []
        read_log = []

        i = 0
        for line in contents.split("\n"):
            i += 1
            if line.startswith("access_type;"):
                continue
            if len(line) == 0:
                continue

            fields = line.split(";")
            if len(fields) != 3:
                self.print("error", f"Unexpected number of fields ({len(fields)} instead of 3) in csv line {i} in file {ral_modfile.path}")
                continue

            access_type = fields[0].strip()
            log = {
                "resource_rel_path": fields[1].strip(),
                "datetime": fields[2].strip(),
            }

            if access_type == "read":
                read_log.append(log)
            elif access_type == "write":
                write_log.append(log)
            else:
                self.print("error", f"Unexpected access_type {access_type} in csv line {i} in file {ral_modfile.path}. Expected: read or write.")
                continue

        return write_log, read_log

    def allow_post_module(self, meta_module):
        """Return True if post module is allowed to run after this one, else return False"""
        if meta_module.module_class_name == self.module_class_name:
            return False
        return True

    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def integrate_save(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass
