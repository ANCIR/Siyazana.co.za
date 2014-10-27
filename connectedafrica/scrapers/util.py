import os
import re
import json
import requests
import urlparse
from StringIO import StringIO
from threading import RLock

from scrapekit import Scraper
from unicodecsv import DictWriter, DictReader

from connectedafrica.core import app


ACCEPTED_IMAGE_EXTENSIONS = set(('.png', '.jpg', '.jpeg', '.bmp'))
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
DATA_PATH = os.path.abspath(DATA_PATH)
PERSONS_CSV_URL = 'https://docs.google.com/spreadsheets/d/1HPYBRG899R_WVW5qkvHoUwliU42Czlx8_N1l58XYc7c/export?format=csv&gid=1657155089'


def make_scraper(name, config=None):
    if config is None:
        config = {}
    config['data_path'] = DATA_PATH
    return Scraper(name, config=config)


def make_path(file_name):
    file_path = os.path.join(DATA_PATH, file_name)
    dir_name = os.path.dirname(file_path)
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name)
    return file_path


def make_abs_url(abs_source_url, url):
    '''
    Uses the scheme and domain of abs_source_url to
    make url absolute. If url is already absolute,
    it returns url unchanged.
    '''
    parts = urlparse.urlparse(url)
    if not parts.netloc:
        abs_parts = urlparse.urlparse(abs_source_url)
        url = urlparse.urlunparse(abs_parts[:2] + parts[2:])
    return url


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


def set_to_empty(data, empty_keys=(), empty_values=('', ), empty_value=None):
    '''
    Adds empty_keys to data with value empty_value if the key is not in data.
    Also sets all values in empty_values to empty_value, e.g. for normalizing
    empty strings to None.
    '''
    empty_values = set(empty_values)
    for k, v in data.iteritems():
        if v in empty_values:
            data[k] = empty_value
    for k in empty_keys:
        if k not in data:
            data[k] = empty_value


def gdocs_persons():
    resp = requests.get(PERSONS_CSV_URL, stream=True)
    resp.raise_for_status()
    reader = DictReader(resp.raw)
    for data in reader:
        if not data['Full Name']:
            continue
        yield data


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
