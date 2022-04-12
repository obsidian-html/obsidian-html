from appdirs import AppDirs

class Ledger:
    ledger = None

    def __init__(self):
        self.ledger = {}
        self.ledger['vault_path'] = ''
        self.ledger['entrypoint_path'] = ''
        self.ledger['markdown_folder_path'] = ''
        self.ledger['markdown_entrypoint_path'] = ''
        self.ledger['repo_folder_path'] = ''
        self.ledger['config_folder_path'] = AppDirs("obsidianhtml", "obsidianhtml").user_config_dir

        self.ledger['gitpages_configured'] = False
        self.ledger['test'] = 0

    def get(self, value_id):
        # Get value
        if value_id not in self.ledger.keys():
            raise Exception(f'key {value_id} not present in ledger')

        value = self.ledger[value_id]

        # Set default
        return value

    def set_value(self, id, value):
        if id == 'vault_path':
            return self.set_vault_path(value)
        elif id == 'entrypoint_path':
            return self.set_entrypoint_path(value)
        elif id == 'config_folder_path':
            return self.set_config_folder_path(value)
        elif id == 'markdown_folder_path':
            return self.set_markdown_folder_path(value)
        elif id == 'markdown_entrypoint_path':
            return self.set_markdown_entrypoint_path(value)
        elif id == 'repo_folder_path':
            return self.set_repo_folder_path(value)            
        elif id == 'gitpages_configured':
            return self.set_gitpages_configured(value)
        else:
            raise Exception(f'id {id} not known (Ledger.set_value())')

    def set_vault_path(self, value):
        self.ledger['vault_path'] = value
    def set_entrypoint_path(self, value):
        self.ledger['entrypoint_path'] = value
    def set_config_folder_path(self, value):
        self.ledger['config_folder_path'] = value        
    def set_markdown_folder_path(self, value):
        self.ledger['markdown_folder_path'] = value 
    def set_markdown_entrypoint_path(self, value):
        self.ledger['markdown_entrypoint_path'] = value
    def set_gitpages_configured(self, value):
        self.ledger['gitpages_configured'] = value
    def set_repo_folder_path(self, value):
        self.ledger['repo_folder_path'] = value