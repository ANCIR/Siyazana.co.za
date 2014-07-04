import os
import re
import json
from threading import RLock
from unicodecsv import DictWriter

from connectedafrica.core import app


DATA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
DATA_PATH = os.path.abspath(DATA_PATH)


def clean_space(text):
    if text is None:
        return None
    text = re.sub('\s+', ' ', text)
    return text.strip()


def make_path(file_name):
    file_path = os.path.join(DATA_PATH, file_name)
    dir_name = os.path.dirname(file_path)
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name)
    return file_path


def read_json(file_name):
    file_path = make_path(file_name)
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'rb') as fh:
        return json.load(fh)


def write_json(file_name, data):
    file_path = make_path(file_name)
    with open(file_path, 'wb') as fh:
        return json.dump(data.copy(), fh)


class ScraperException(Exception):
    pass


class MultiCSV(object):

    def __init__(self):
        self.fhs = {}
        self.writers = {}
        self.lock = RLock()

    def write(self, file_name, row):
        with self.lock:
            if file_name not in self.fhs:
                self.fhs[file_name] = open(make_path(file_name), 'wb')
                dw = DictWriter(self.fhs[file_name], row.keys())
                self.writers[file_name] = dw
                dw.writeheader()

            self.writers[file_name].writerow(row)

    def close(self):
        for fh in self.fhs.values():
            fh.close()
