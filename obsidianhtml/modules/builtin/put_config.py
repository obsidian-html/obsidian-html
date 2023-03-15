from .. import ObsidianHtmlModule

class PutConfigModule(ObsidianHtmlModule):
    """
    This module will load the config yaml as provided by the user, it will then get the default config from ObsidianHtml and merge the two.
    """
    @property
    def requires(self):
        return tuple()
    @property
    def provides(self):
        return tuple(['config.yml'])
    @property
    def alters(self):
        return tuple()

    # def loadConfig(self):
    #     # find correct config yaml
    #     if self.user_config_dict is None:
    #         input_yml_path_str = find_user_config_yaml_path(config_yaml_location)
    #     else:
    #         input_yml_path_str = ""

    #     # create config object based on config yaml
    #     self.config = Config(self, input_yml_path_str)

    #     # build up config object further
    #     self.config.LoadIncludedFiles()
    #     self.configured_html_prefix = self.gc("html_url_prefix")

    def run(self):
        pass

    def run2(self):
        self.print('error', f'AAAAaaa {self.module_name}')
        return True