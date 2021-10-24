class PicknickBasket:
    files = None           
    tagtree = None
    config = None
    paths = None
    html_template = None

    def __init__(self, config, paths):
        self.config = config
        self.tagtree = {'notes': [], 'subtags': {}}
        self.paths = paths