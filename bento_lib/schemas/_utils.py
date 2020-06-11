import json
import os


DIR_PATH = os.path.dirname(os.path.realpath(__file__))


def load_json_schema(name):
    with open(os.path.join(DIR_PATH, name)) as f:
        return json.load(f)
