import logging
import json
import os
#from pprint import pprint
#from itertools import count
from urlparse import urljoin

from lxml import html
from thready import threaded
import requests

from connectedafrica.scrapers.util import MultiCSV
from connectedafrica.scrapers.util import make_path, clean_space


log = logging.getLogger('npo')
URL_PATTERN = "http://www.npo.gov.za/PublicNpo/Npo/DetailsAllDocs/%s"


def make_cache(i):
    return make_path('.cache/npo/%s/%s/%s/%s/%s.json' % (
        i % 10, i % 100, i % 1000, i % 10000, i))


def make_urls():
    for i in xrange(1, 16000000):
        yield i


def scrape_npo(csv, i):
    url = URL_PATTERN % i
    cache_path = make_cache(i)
    if not os.path.exists(cache_path):
        res = requests.get(url)
        page = {
            'url': url,
            'http_status': res.status_code,
            'content': res.content.decode('utf-8')
        }
        with open(cache_path, 'wb') as fh:
            json.dump(page, fh)
    else:
        with open(cache_path, 'rb') as fh:
            page = json.load(fh)
    if 'internal server error' in page['content']:
        return
    data = {}
    doc = html.fromstring(page['content'])
    data = {
        'source_url': url,
        'name': doc.find('.//h1').find('.//span').text.strip(),
        'status': doc.find('.//h1').find('.//span[@class="npo-status"]').text,
        'email': None
    }
    log.info("Scraping: %s", data['name'])
    sub_titles = doc.findall('.//h5')
    next_heading = None
    for sub_title in sub_titles:
        text = clean_space(sub_title.text)
        if 'Registration No' in text:
            data['reg_no'] = sub_title.find('./span').text.strip()
            next_heading = 'category'
        elif 'Your Name' in text:
            next_heading = None
        elif next_heading == 'category':
            data['category'] = text
            next_heading = 'legal_form'
        elif next_heading == 'legal_form':
            data['legal_form'] = text
    for span in doc.findall('.//span'):
        text = clean_space(span.text)
        if text is not None and 'Registered on' in text:
            data['reg_date'] = text
    for addr in doc.findall('.//div[@class="address"]'):
        addr_type = clean_space(addr.find('./h4').text)
        addrs = [clean_space(a) for a in addr.xpath('string()').split('\n')]
        addrs = '\n'.join([a for a in addrs if len(a)][1:])
        if 'Physical' in addr_type:
            data['physical_address'] = addrs
        elif 'Postal' in addr_type:
            data['postal_address'] = addrs
        elif 'Contact' in addr_type:
            data['contact_name'] = clean_space(addr.find('./p').text)
            for li in addr.findall('.//li'):
                contact = clean_space(li.xpath('string()'))
                contact_type = {
                    'phone': 'phone',
                    'mailinfo': 'email',
                    'fax': 'fax'
                }.get(li.get('class'))
                data[contact_type] = contact
    off_div = './/li[@data-sha-context-enttype="Npo.AppointedOfficeBearer"]'
    csv.write('npo_organisations.csv', data)
    for li in doc.findall(off_div):
        s = li.find('.//strong')
        a = s.find('./a')
        id_number = li.find('.//div/span')
        if id_number is not None:
            id_number = id_number.text
            id_number = id_number.replace('(', '')
            id_number = id_number.replace(')', '')
            id_number = id_number.strip()
            if 'Neither ID or Passport' in id_number:
                id_number = None
        officer = {
            'role': clean_space(s.text).replace(' :', ''),
            'npo_name': data['name'],
            'source_url': url,
            'officer_id': urljoin(url, a.get('href')),
            'officer_name': clean_space(a.text),
            'officer_id_number': id_number
        }
        csv.write('npo_officers.csv', officer)


def scrape_npos():
    csv = MultiCSV()
    threaded(make_urls(), lambda i: scrape_npo(csv, i), num_threads=30)
    csv.close()

if __name__ == '__main__':
    scrape_npos()
