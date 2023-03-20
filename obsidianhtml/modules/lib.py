import json


def verbose_enough(level, verbosity):
    verbosity_ranks = {
        "quiet": 0,
        "error": 10,
        "deprecation": 20,
        "info": 30,
        "debug": 100,
    }
    verbosity_rank_set = verbosity_ranks[verbosity.lower()]
    verbosity_rank_current = verbosity_ranks[level.lower()]
    verbose_enough = verbosity_rank_current <= verbosity_rank_set
    return verbose_enough


class hash_wrap:
    """This class exists so that we can pass in dicts to cached functions"""

    def __init__(self, dict_obj):
        self.dict = dict_obj

    def __getitem__(self, item):
        return self.dict[item]

    def __contains__(self, key):
        return key in self.dict

    def __iter__(self):
        return self.dict.__iter__()
    def keys(self):
        return self.dict.keys()
    def unwrap(self):
        return self.dict


def pprint_json(obj):
    from json import JSONEncoder

    class class_encoder(JSONEncoder):
        def default(self, o):
            return o.__name__

    print(json.dumps(obj, indent=2, cls=class_encoder))
