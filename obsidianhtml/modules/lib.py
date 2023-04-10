import json

verbosity_ranks = {
    "quiet": 0,
    "error": 10,
    "warning": 15,
    "deprecation": 20,
    "info": 30,
    "debug": 100,
}


def verbose_enough(verbosity_requested, verbosity_threshold):
    # if verbosity_threshold is None:
    #     verbosity_threshold = "error"
    verbosity_rank_threshold = verbosity_ranks[verbosity_threshold.lower()]
    verbosity_rank_current = verbosity_ranks[verbosity_requested.lower()]
    verbose_enough = verbosity_rank_current <= verbosity_rank_threshold
    return verbose_enough


def format_logrule(verbosity, message, source=None):
    if verbosity.lower() not in verbosity_ranks.keys():
        raise Exception(f"Verbosity of {verbosity} is not a valid verbosity.")

    if type(message) is tuple:
        message = " ".join(message)
    verbosity = verbosity.upper()
    source_line = ""
    if source is not None:
        source_line = f"{source} ::"

    return f"[ {verbosity:^5} ] {source_line} {message}"


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
