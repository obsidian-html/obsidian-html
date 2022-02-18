import json
from datetime import date

class NetworkTree:
    verbose = None
    tree = None

    def __init__(self, verbose):
        self.verbose = verbose
        self.tree = {'nodes': [], 'links': []}
        self.node_lookup = {}

    def NewNode(self):
        return {'id': '', 'group': 1, 'url': '', 'metadata': {}}

    def NewLink(self):
        return {'source': '', 'target': '', 'value': 1}        

    def AddNode(self, node_obj):
        if self.verbose:
            print("Received node", node_obj)
        # Skip if already present
        for node in self.tree['nodes']:
            if node['id'] == node_obj['id']:
                if self.verbose:
                    print("Node already present")
                return
        
        # Add node
        self.tree['nodes'].append(node_obj)
        if self.verbose:
            print("Node added")

    def AddLink(self, link_obj):
        if self.verbose:
            print("Received link", link_obj)
        # Skip if already present        
        for link in self.tree['links']:
            if link['source'] == link_obj['source'] and link['target'] == link_obj['target']:
                if self.verbose:
                    print("Link already present")
                return

        # Add link
        self.tree['links'].append(link_obj) 
        if self.verbose:
            print("Link added")

    def compile_node_lookup(self):
        for n in self.tree['nodes']:
            self.node_lookup[n['id']] = n
    
    def OutputJson(self):
        tree = StringifyDateRecurse(self.tree.copy())
        return json.dumps(tree)


def StringifyDateRecurse(tree):

    if isinstance(tree, dict):
        for key, value in tree.items():
            if isinstance(value, date):
                tree[key] = value.isoformat()
            elif isinstance(value, list) or isinstance(value, dict):
                tree[key] = StringifyDateRecurse(value)
    if isinstance(tree, list):
        for key, value in enumerate(tree):
            if isinstance(value, date):
                tree[key] = value.isoformat()
            elif isinstance(value, list) or isinstance(value, dict):
                tree[key] = StringifyDateRecurse(value)

    return tree