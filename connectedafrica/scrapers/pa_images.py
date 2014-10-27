import os, re, sys
from datetime import datetime
import urlparse

from lxml import html
import requests
from thready import threaded

from connectedafrica.scrapers.util import (ScraperException, MultiCSV,
                                           gdocs_persons,
                                           ACCEPTED_IMAGE_EXTENSIONS)


THREAD_COUNT = 10


def _scrape_from_pa():
    pass


def _scrape_from_google():
    pass


def _scrape_from_whoswho():
    pass


VALID_ENDPOINTS = {
    "www.pa.org.za": _scrape_from_pa,
    "www.google.co.za": _scrape_from_google,
    "whoswho.co.za": _scrape_from_whoswho
}


def scrape_image(name, url, csv):
    parts = urlparse.urlparse(url)
    extension = os.path.splitext(parts.path)[1]
    if not extension:
        scrape_func = VALID_ENDPOINTS.get(parts.netloc, None)
        if scrape_func is None:
            raise ScraperException("Cannot scrape image from %s" % url)
        url = scrape_func(url)
    elif extension not in ACCEPTED_IMAGE_EXTENSIONS:
        return

    csv.write('pa/pa_images.csv', {
        'name': name,
        'image_url': url
    })


def scrape():
    csv = MultiCSV()
    threaded(
        gdocs_persons(),
        lambda data: scrape_image(data['Full Name'], data['Image URL'], csv),
        num_threads=THREAD_COUNT
    )
    csv.close()


if __name__ == '__main__':
    scrape()
