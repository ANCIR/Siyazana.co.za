import os
import time
from operator import itemgetter

import requests
from thready import threaded
from unicodecsv import csv

from connectedafrica.core import grano
from connectedafrica.scrapers.util import MultiCSV, DATA_PATH


ACCEPTED_EXTENSIONS = set(('.png', '.jpg', '.jpeg', '.bmp'))
ENDPOINT_URL = 'http://en.wikipedia.org/w/api.php'
DEFAULT_PARAMS = {
    'format': 'json',
    'action': 'query',
    'generator': 'search',
    'gsrlimit': 20,
    'gsrnamespace': 6,  # for files
    'prop': 'imageinfo',
    'iiprop': 'size|timestamp|url',
    'indexpageids': ''
}
TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
THREAD_COUNT = 10


def search_wikipedia(name):
    params = DEFAULT_PARAMS.copy()
    params['gsrsearch'] = name
    response = requests.get(ENDPOINT_URL, params=params)
    return response.json()


def scrape_image(name, csv):
    data = search_wikipedia(name)
    # return if no results
    if 'pages' not in data['query']:
        return

    results = data['query']['pages']
    for k in results.keys():
        result = results[k]
        if os.path.splitext(result['imageinfo'][0]['url'])[1] \
                not in ACCEPTED_EXTENSIONS:
            del results[k]
    # in case we have no valid image files
    if len(results) == 0:
        return

    results_order = data['query']['pageids']
    rank_by_search = dict((pageid, 1 if i < 5 else (2 if i < 10 else 3))
                          for i, pageid in enumerate(results_order))
    rank_by_age = [(k, -time.mktime(time.strptime(v['imageinfo'][0]['timestamp'],
                                    TIMESTAMP_FORMAT)))
                   for k, v in results.iteritems()]
    rank_by_age = dict((v[0], i) for i, v in
                       enumerate(sorted(rank_by_age, key=itemgetter(1))))
    ranked_urls = [(k, v['imageinfo'][0]['url']) for k, v in results.iteritems()]
    ranked_urls.sort(key=lambda x: rank_by_search[x[0]] * 100 + rank_by_age[x[0]])
    csv.write('wikipedia_images.csv',
              {'name': name, 'image_url': ranked_urls[0][1]})


def make_names_from_persons_csv():
    with open(os.path.join(DATA_PATH, 'persons.csv')) as f:
        reader = csv.reader(f)
        row = next(reader)
        name_index = row.index('Full Name')
        for row in csv.reader(f):
            yield row[name_index]


def make_names_from_person_entities():
    persons = grano.entities.query().filter('schema', 'Person').results
    for person in persons:
        yield person.properties['name']['value']


def scrape():
    csv = MultiCSV()
    threaded(make_names_from_person_entities(),
             lambda name: scrape_image(name, csv),
             num_threads=THREAD_COUNT)
    csv.close()


if __name__ == '__main__':
    scrape()
