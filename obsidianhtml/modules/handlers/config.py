from functools import cache


@cache
def get_config_cached(config_dict, path: str):
    return get_config(config_dict, path)


def get_config(config_dict, path: str):
    keys = [x for x in path.strip().split("/") if x != ""]

    value = config_dict
    path = []
    for key in keys:
        path.append(key)
        try:
            value = value[key]
        except KeyError:
            print(path)
            raise Exception(f"INTERNAL ERROR: Config setting '{'/'.join(path)}' not found in config.")
    return value
