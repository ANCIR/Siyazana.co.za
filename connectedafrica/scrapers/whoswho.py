import re
import urlparse

from lxml import html
import requests


class ScraperException(Exception):
    pass


class Scraper(object):

    endpoint_url = 'http://whoswho.co.za/'

    def __init__(self, profile_url):
        self.profile_url = profile_url

    def scrape(self, degrees=0, url=None, scraped_urls=None):
        if url is None:
            url = self.profile_url
        if scraped_urls is None:
            scraped_urls = set()

        abs_url = self.get_absolute_url(url)
        if abs_url in scraped_urls:
            return
        data = self.get_data(abs_url)
        scraped_urls.add(abs_url)
        yield data

        if degrees > 0:
            for related_profile in data['related_profiles']:
                for data in self.scrape(degrees - 1, related_profile['url'],
                                        scraped_urls):
                    yield data

    def get_absolute_url(self, url):
        if not url.startswith(Scraper.endpoint_url):
            parts = urlparse.urlparse(url)
            if parts.scheme == 'https':
                raise ScraperException("Who's Who does not accept https connections")
            elif parts.netloc:
                raise ScraperException("'%s' is not a Who's Who URL" % url)
            return urlparse.urlunparse(['http', 'whoswho.co.za'] + list(parts[2:]))
        return url

    def parse_content(self, content):
        data = {
            'related_profiles': []
        }
        root = html.fromstring(content)

        # get the related profile info
        related_el = root.get_element_by_id('related')
        if related_el is not None:
            for el in related_el.find_class('item'):
                a_el = el.xpath('a')[0]
                related_data = {'url': a_el.get('href')}
                img_el = a_el.xpath('img')
                if len(img_el) > 0:
                    img_el = img_el[0]
                    related_data['image_url'] = img_el.get('src')
                    related_data['title'] = img_el.get('title')
                data['related_profiles'].append(related_data)

        return data

    def get_data(self, abs_url):
        response = requests.get(abs_url)
        response.raise_for_status()

        whoswho_id = abs_url.rsplit('-', 1)[-1]
        try:
            whoswho_id = int(whoswho_id)
        except ValueError:
            whoswho_id = None

        data = self.parse_content(response.text)
        data['whoswho_id'] = whoswho_id
        data['url'] = abs_url
        return data
