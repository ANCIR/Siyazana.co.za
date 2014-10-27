import os
import urlparse

from lxml import html
import requests
from thready import threaded

from connectedafrica.scrapers.util import (ScraperException, MultiCSV,
                                           gdocs_persons, make_abs_url,
                                           ACCEPTED_IMAGE_EXTENSIONS)


THREAD_COUNT = 10


def get_document_root(url):
    response = requests.get(url)
    response.raise_for_status()
    return html.fromstring(response.text)


def _scrape_from_pa(url):
    root = get_document_root(url)
    pic_el = root.find_class('profile-pic')
    if pic_el:
        pic_el = pic_el[0].xpath('img[1]')
        if pic_el:
            return pic_el[0].get('src')
    raise ScraperException("Image not found at %s" % url)


def _scrape_from_google(url):
    raise NotImplementedError
    root = get_document_root(url)


def _scrape_from_whoswho(url):
    raise NotImplementedError
    root = get_document_root(url)


def _scrape_from_wikipedia(url):
    raise NotImplementedError
    root = get_document_root(url)


VALID_ENDPOINTS = {
    "www.pa.org.za": _scrape_from_pa,
    "www.google.co.za": _scrape_from_google,
    "whoswho.co.za": _scrape_from_whoswho,
    "en.wikipedia.org": _scrape_from_wikipedia
}


def scrape_image(name, url, csv):
    print "scraping %s" % name
    parts = urlparse.urlparse(url)
    extension = os.path.splitext(parts.path)[1]
    if not extension:
        scrape_func = VALID_ENDPOINTS.get(parts.netloc, None)
        if scrape_func is None:
            raise ScraperException("Cannot scrape image from %s" % parts.netloc)
        image_url = scrape_func(url)
        url = make_abs_url(url, image_url)
    elif extension not in ACCEPTED_IMAGE_EXTENSIONS:
        raise ScraperException("Unsupported image format at %s" % url)

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
