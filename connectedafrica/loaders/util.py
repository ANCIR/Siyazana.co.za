import os
import json

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
DATA_PATH = os.path.abspath(DATA_PATH)


def read_json(file_name):
    file_path = os.path.join(DATA_PATH, file_name)
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'rb') as fh:
        return json.load(fh)


def write_json(file_name, data):
    file_path = os.path.join(DATA_PATH, file_name)
    with open(file_path, 'wb') as fh:
        return json.dump(data.copy(), fh)
