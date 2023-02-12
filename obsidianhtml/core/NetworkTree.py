import json
from datetime import date
from ..lib import slugify_path

"""
This class helps us building the graph.json by keeping track of which notes link to other notes.
Here, a note is a "node" (hah), and a note linking to another note is a link. 
For every note we also save its metadata, so that this information is available at later steps.
"""


class NetworkTree:
    tree = None
    nid_inc = 0

    def __init__(self, index):
        # register
        self.index = index
        self.pb = index.pb

        self.tree = {"nodes": [], "links": []}
        self.node_lookup = {}
        self.node_lookup_slug = {}

        self.node_graph = None
        self.node_graph_lookup = None

    # TYPES
    # ===============================================================================================
    def NewNode(self):
        return {"id": "", "nid": None, "group": 1, "url": "", "metadata": {}, "links": [], "outward_links": [], "inward_links": []}

    def NewLink(self):
        return {"source": "", "target": "", "value": 1}

    # INTERFACE
    # ===============================================================================================
    def add_file_object_to_node_list(self, fo, backlink_node=None, link_type="reference"):
        # shorthand
        pb = fo.pb
        md = fo.md
        rel_dst_path = md.fo.path["html"]["file_relative_path"]

        # Get simple dict template
        node = pb.index.network_tree.NewNode()

        # add all metadata to node, so we can access it later when we need to, once compilation of html is complete
        node["metadata"] = md.metadata.copy()

        # Use filename as node id, unless 'graph_name' is set in the yaml frontmatter
        node["id"] = pb.FileFinder.GetNodeId(pb, md.fo.path["markdown"]["file_relative_path"].as_posix())
        node["name"] = md.GetNodeName()

        # Url is used so you can open the note/node by clicking on it
        node["url"] = md.fo.get_link("html")
        node["rtr_url"] = rel_dst_path.as_posix()
        pb.index.network_tree.add_node(node)

        # Backlinks are set so when recursing, the links (edges) can be determined
        if backlink_node is not None:
            link = pb.index.network_tree.NewLink()
            link["source"] = backlink_node["id"]
            link["target"] = node["id"]
            link["type"] = link_type
            pb.index.network_tree.AddLink(link)

        # return node so that it can be set as the next backlink_node
        return node

    def add_node(self, node_obj):
        """Add node to network tree"""
        if self.pb.verbose:
            print("Received node", node_obj)
        # Skip if already present
        for node in self.tree["nodes"]:
            if node["id"] == node_obj["id"]:
                node["metadata"] = node_obj["metadata"].copy()
                if self.pb.verbose:
                    print("Node already present")
                return

        # Add node
        self.nid_inc += 1
        node_obj["nid"] = self.nid_inc

        self.tree["nodes"].append(node_obj)
        if self.pb.verbose:
            print("Node added")

    def AddLink(self, link_obj):
        if self.pb.verbose:
            print("Received link", link_obj)
        # Skip if already present
        for link in self.tree["links"]:
            if link["source"] == link_obj["source"] and link["target"] == link_obj["target"]:
                if self.pb.verbose:
                    print("Link already present")
                return

        # Add link
        self.tree["links"].append(link_obj)
        if self.pb.verbose:
            print("Link added")

    def OutputJson(self):
        """the graph.json"""
        tree = StringifyDateRecurse(self.tree.copy())
        return json.dumps(tree)

    # METHODS
    # ===============================================================================================
    def compile_node_lookup(self):
        for n in self.tree["nodes"]:
            self.node_lookup[n["id"]] = n
            self.node_lookup_slug[slugify_path(n["id"])] = n

    def AddCrosslinks(self):
        for link in self.tree["links"]:
            src = self.node_lookup[link["source"]]
            dst = self.node_lookup[link["target"]]

            src["links"].append(dst["id"])
            src["outward_links"].append(dst["id"])
            dst["links"].append(src["id"])
            dst["inward_links"].append(src["id"])

        # remove duplicates from links
        for node in self.tree["nodes"]:
            node["links"] = list(dict.fromkeys(node["links"]))

    def CompileNoteGraphDataStructure(self):
        d = {"id": "", "title": "", "linkTo": None, "referencedBy": None}
        note_lookup = {}
        note_graph = []
        for node in self.tree["nodes"]:
            di = d.copy()
            di["id"] = node["nid"]
            di["title"] = node["id"]
            di["linkTo"] = []
            di["referencedBy"] = []
            note_graph.append(di)
            note_lookup[node["id"]] = di

        for link in self.tree["links"]:
            src = note_lookup[link["source"]]
            dst = note_lookup[link["target"]]
            if src["id"] not in dst["referencedBy"]:
                dst["referencedBy"].append(src["id"])
            if dst["id"] not in src["linkTo"]:
                src["linkTo"].append(dst["id"])

        self.node_graph = note_graph
        self.node_graph_lookup = note_lookup

    def OutputNodeGraphJson(self):
        """the graph.json"""
        node_graph = StringifyDateRecurse(self.node_graph.copy())
        return json.dumps(node_graph)


def StringifyDateRecurse(tree):
    """We can't convert a date type to json, so we have to manually convert any dates in the tree to isoformatted date strings"""
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
