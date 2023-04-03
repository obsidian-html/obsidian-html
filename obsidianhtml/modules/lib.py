import json


def verbose_enough(verbosity_requested, verbosity_threshold):
    verbosity_ranks = {
        "quiet": 0,
        "error": 10,
        "deprecation": 20,
        "info": 30,
        "debug": 100,
    }
    verbosity_rank_threshold = verbosity_ranks[verbosity_threshold.lower()]
    verbosity_rank_current = verbosity_ranks[verbosity_requested.lower()]
    verbose_enough = verbosity_rank_current <= verbosity_rank_threshold
    return verbose_enough


class hash_wrap:
    """This class exists so that we can pass in dicts to cached functions"""

    def __init__(self, dict_obj):
        self.dict = dict_obj

    def __getitem__(self, item):
        return self.dict[item]

    def __setitem__(self, key, newvalue):
        self.dict[key] = newvalue

    def __contains__(self, key):
        return key in self.dict

    def __iter__(self):
        return self.dict.__iter__()

    def keys(self):
        return self.dict.keys()

    def items(self):
        return self.dict.items()

    def unwrap(self):
        return self.dict



def pprint_json(obj):
    from json import JSONEncoder

    class class_encoder(JSONEncoder):
        def default(self, o):
            return o.__name__

    print(json.dumps(obj, indent=2, cls=class_encoder))
