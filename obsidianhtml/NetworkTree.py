import json
from datetime import date

'''
This class helps us building the graph.json by keeping track of which notes link to other notes.
Here, a note is a "node" (hah), and a note linking to another note is a link. 
For every note we also save its metadata, so that this information is available at later steps.
'''

class NetworkTree:
    verbose = None
    tree = None
    nid_inc = 0

    def __init__(self, verbose):
        self.verbose = verbose
        self.tree = {'nodes': [], 'links': []}
        self.node_lookup = {}

        self.node_graph = None
        self.node_graph_lookup = None

    def NewNode(self):
        return {'id': '', 'nid': None, 'group': 1, 'url': '', 'metadata': {}, 'links': [], 'outward_links':[], 'inward_links':[]}

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
        self.nid_inc += 1
        node_obj['nid'] = self.nid_inc

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
    
    def AddCrosslinks(self):
        for link in self.tree['links']:
            src = self.node_lookup[link['source']]
            dst = self.node_lookup[link['target']]

            src['links'].append(dst['id'])
            src['outward_links'].append(dst['id'])
            dst['links'].append(src['id'])
            dst['inward_links'].append(src['id'])

        # remove duplicates from links
        for node in self.tree['nodes']:
            node['links'] = list(dict.fromkeys(node['links']))

    def OutputJson(self):
        ''' the graph.json '''
        tree = StringifyDateRecurse(self.tree.copy())
        return json.dumps(tree)


    def CompileNoteGraphDataStructure(self):
        d = {'id': '', 'title': '', 'linkTo': None, 'referencedBy': None}
        id_lookup = {}
        note_lookup = {}
        note_graph = []
        for node in self.tree['nodes']:
            di = d.copy()
            di['id'] = node['nid']
            di['title'] = node['id']
            di['linkTo'] = []
            di['referencedBy'] = []
            note_graph.append(di)
            note_lookup[node['id']] = di
        
        for link in self.tree['links']:
            src = note_lookup[link['source']]
            dst = note_lookup[link['target']]
            if src['id'] not in dst['referencedBy']:
                dst['referencedBy'].append(src['id'])
            if dst['id'] not in src['linkTo']:
                src['linkTo'].append(dst['id'])

        self.node_graph = note_graph
        self.node_graph_lookup = note_lookup
    
    def OutputNodeGraphJson(self):
        ''' the graph.json '''
        node_graph = StringifyDateRecurse(self.node_graph.copy())
        return json.dumps(node_graph)


def StringifyDateRecurse(tree):
    ''' We can't convert a date type to json, so we have to manually convert any dates in the tree to isoformatted date strings '''
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