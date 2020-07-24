import json
import os
from copy import deepcopy


def replace_key(dct_ptr, attribute, value):
    if attribute[0] not in dct_ptr:
        dct_ptr[attribute[0]] = {}
    if len(attribute) == 1:
        dct_ptr[attribute[0]] = value
    else:
        replace_key(dct_ptr[attribute[0]], attribute[1:], value)


def read_json(path: str):
    with open(path) as json_file:
        return json.load(json_file)


def override_dict(d: dict, u: dict):
    result = deepcopy(d)
    for k, v in u.items():
        if isinstance(v, dict):
            result[k] = override_dict(d.get(k, {}), v)
        else:
            result[k] = v
    return result


def get_config(config_path: str) -> dict:
    config_env = os.environ['ENV']

    config = override_dict(
        read_json(f'{config_path}/default.json'),
        read_json(f'{config_path}/{config_env}.json'),
    )

    for key, value in os.environ.items():
        attribute = key.lower().split('__')
        replace_key(config, attribute, value)

    return config
