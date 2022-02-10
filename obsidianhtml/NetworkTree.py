import json

class NetworkTree:
    verbose = None
    tree = None

    def __init__(self, verbose):
        self.verbose = verbose
        self.tree = {'nodes': [], 'links': []}
        self.node_lookup = {}

    def NewNode(self):
        return {'id': '', 'group': 1, 'url': ''}

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
        return json.dumps(self.tree)


        