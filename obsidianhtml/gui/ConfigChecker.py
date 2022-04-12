class ConfigChecker:
    main_api = None
    ledger = None
    def __init__(self, main_api):
        self.main_api = main_api
        self.ledger = main_api.ledger

    def DetermineDefaultConfigFolderPath(self):
        config_folder_path = dirs = AppDirs("obsidianhtml", "obsidianhtml")

    def presetConfigPath(self):
        # get configured value
        config_folder_path = self.ledger.get('config_folder_path')

        if config_folder_path == '':
            config_folder_path = self.DetermineDefaultConfigFolderPath()
            self.ledger.set_value('config_folder_path', config_folder_path)
        
    def presetRepoClonePath(self, repo_name):
        value = self.ledger.get('repo_folder_path')
        if value == '':
            folder = Path.home().as_posix()
            if Path.home().joinpath('git').exists():
                folder = Path.home().joinpath('git').as_posix()
            elif Path.home().joinpath('Git').exists():
                folder = Path.home().joinpath('Git').as_posix()

            self.ledger.set_value('repo_folder_path', Path(folder).joinpath(repo_name).as_posix())  