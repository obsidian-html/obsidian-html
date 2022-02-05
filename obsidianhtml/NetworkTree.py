import json

class NetworkTree:
    conf = None
    tree = None

    def __init__(self, conf):
        self.conf = conf
        self.tree = {'nodes': [], 'links': []}

    def NewNode(self):
        return {'id': '', 'group': 1, 'url': ''}

    def NewLink(self):
        return {'source': '', 'target': '', 'value': 1}        

    def AddNode(self, node_obj):
        if self.conf['toggles']['verbose_printout']:
            print("Received node", node_obj)
        # Skip if already present
        for node in self.tree['nodes']:
            if node['id'] == node_obj['id']:
                if self.conf['toggles']['verbose_printout']:
                    print("Node already present")
                return
        
        # Add node
        self.tree['nodes'].append(node_obj)
        if self.conf['toggles']['verbose_printout']:
            print("Node added")

    def AddLink(self, link_obj):
        if self.conf['toggles']['verbose_printout']:
            print("Received link", link_obj)
        # Skip if already present        
        for link in self.tree['links']:
            if link['source'] == link_obj['source'] and link['target'] == link_obj['target']:
                if self.conf['toggles']['verbose_printout']:
                    print("Link already present")
                return

        # Add link
        self.tree['links'].append(link_obj) 
        if self.conf['toggles']['verbose_printout']:
            print("Link added")
    
    def OutputJson(self):
        return json.dumps(self.tree)


        