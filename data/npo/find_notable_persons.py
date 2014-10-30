# coding: utf8
import json
import os
import re
import string
import sys

from Levenshtein import distance
from unicodecsv import DictReader, DictWriter
from unidecode import unidecode

from connectedafrica.scrapers.util import gdocs_persons, DATA_PATH


PUNCTCTRL_RE = re.compile(ur'[%s\u0000-\u0008\u000A-\u001F\u007F]'
                          % re.escape(string.punctuation), re.UNICODE)


class FingerprintStorage(object):
    '''
    Store fingerprints in buckets. This splits them up into words and
    puts them in buckets keyed by each word's first letter. About
    double as fast as brute force.
    '''
    def __init__(self):
        self.buckets = {}
        self.id_to_bucket = {}

    def put(self, id, fingerprint):
        parts = fingerprint.split()
        for part in parts:
            self.buckets.setdefault(part[0], {})
            self.buckets[part[0]][id] = fingerprint
        if not fingerprint:
            raise ValueError("Empty fingerprint for id %s" % id)
        self.id_to_bucket[id] = fingerprint[0]

    def get(self, id):
        return self.buckets[self.id_to_bucket[id]][id]

    def get_all(self, fingerprint):
        parts = fingerprint.split()
        matching_buckets = {}
        for part in parts:
            matching_buckets.update(self.buckets[part[0]])
        return matching_buckets

    def to_dict(self):
        all_data = {}
        for bucket in self.buckets.values():
            all_data.update(bucket)
        return all_data

    @classmethod
    def from_dict(cls, data):
        storage = cls()
        for id, fingerprint in data.iteritems():
            storage.put(id, fingerprint)
        return storage


def make_fingerprint(name):
    '''
    Uses algorithm here:
    https://github.com/OpenRefine/OpenRefine/wiki/Clustering-In-Depth#fingerprint
    '''
    name = name.strip()
    name = name.lower()
    name = PUNCTCTRL_RE.sub(u'', name)
    fragments = set(name.split())
    name = u' '.join(sorted(fragments))
    return unicode(unidecode(name))


def _get_cache_path(path):
    import hashlib
    m = hashlib.md5()
    with open(path) as f:
        m.update(f.read())
    try:
        os.mkdir(os.path.join(DATA_PATH, 'npo/.cache/'))
    except OSError:
        pass
    return os.path.join(DATA_PATH, 'npo/.cache/%s.json' % m.hexdigest())


def get_all_officer_fingerprints():
    officer_csv_path = os.path.join(DATA_PATH, 'npo/npo_officers.csv')
    # check cache
    cache_path = _get_cache_path(officer_csv_path)
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return FingerprintStorage.from_dict(json.loads(f.read()))

    fingerprints = FingerprintStorage()
    total = sum(1 for line in open(officer_csv_path))
    sys.stderr.write("\nMaking officer fingerprints...\n")

    with open(officer_csv_path) as f:
        reader = DictReader(f)
        for i, data in enumerate(reader):
            officer_id = data['officer_id'].strip()
            officer_name = data['officer_name'].strip()
            if not (officer_id and officer_name):
                continue
            fingerprints.put(officer_id, make_fingerprint(officer_name))
            sys.stderr.write("\r%d of %d" % (i + 1, total))
            sys.stderr.flush()

    # write to cache
    with open(cache_path, 'w') as f:
        f.write(json.dumps(fingerprints.to_dict()))

    sys.stderr.write("\nDone\n")
    return fingerprints


def find_matching_officers(fingerprint, officer_fingerprints,
                           excluded_ids=tuple(), min_percentage=0.75):
    matches = set()

    for officer_id, officer_fingerprint in \
            officer_fingerprints.get_all(fingerprint).iteritems():
        if officer_id in excluded_ids:
            continue
        dist = distance(fingerprint, officer_fingerprint)
        length = max(len(fingerprint), len(officer_fingerprint))
        if length == 0:
            percentage = 0.0
        else:
            percentage = 1.0 - dist / float(length)
        if percentage >= min_percentage:
            matches.add(officer_id)

    return matches


def find_notable_officers(min_percentage=0.75):
    notable_officers = set()
    officer_fingerprints = get_all_officer_fingerprints()
    sys.stderr.write("\nFinding matches...\n")
    writer = DictWriter(sys.stdout, ['name', 'fingerprint', 'officer_id',
                                     'fingerprint_officer'])

    for i, data in enumerate(gdocs_persons()):
        fingerprint = make_fingerprint(data['Full Name'])
        matching_ids = find_matching_officers(
            fingerprint,
            officer_fingerprints,
            excluded_ids=notable_officers,
            min_percentage=min_percentage
        )

        for officer_id in matching_ids:
            writer.writerow({
                'name': data['Full Name'],
                'officer_id': officer_id,
                'fingerprint': fingerprint,
                'fingerprint_officer': officer_fingerprints.get(officer_id)
            })

        notable_officers.update(matching_ids)
        sys.stderr.write("\r%d" % (i + 1))
        sys.stderr.flush()

    sys.stderr.write("\nDone\n")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        try:
            percentage = float(sys.argv[1])
            assert 0.0 <= percentage <= 1.0
            find_notable_officers(float(sys.argv[1]))
        except (ValueError, AssertionError):
            sys.stderr.write("\nUsage: python find_notable_officers.py [MIN_PERCENTAGE {0.0 - 1.0}]\n")
    else:
        find_notable_officers()
