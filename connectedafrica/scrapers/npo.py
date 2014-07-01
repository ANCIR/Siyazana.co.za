import re
import logging
from pprint import pprint
from itertools import count
from threading import RLock
from urlparse import urljoin

from lxml import html
from thready import threaded
import requests
import dataset

logging.basicConfig(level=logging.INFO)

log = logging.getLogger()
GEN = 2
lock = RLock()
engine = dataset.connect('sqlite:///npo.db')
pages, orgs, roles = engine['page'], engine['organisation'], engine['role']
URL_PATTERN = "http://www.npo.gov.za/PublicNpo/Npo/DetailsPublicDocs/%s"


def clean_space(text):
    if text is None:
        return None
    text = re.sub('\s+', ' ', text)
    return text.strip()


def make_urls():
    for i in count(1):
        yield URL_PATTERN % i


def scrape_npo(url):
    with lock:
        if orgs.find_one(source_url=url, data_gen=GEN):
            return
        page = pages.find_one(url=url)
    if page is None or page.get('re_check'):
        res = requests.get(url)
        page = {
            'url': url,
            'http_status': res.status_code,
            'content': res.content.decode('utf-8'),
            're_check': False
        }
        with lock:
            pages.insert(page)
    if 'internal server error' in page['content']:
        return
    data = {}
    doc = html.fromstring(page['content'])
    data = {
        'source_url': url,
        'data_gen': GEN,
        'name': doc.find('.//h1').find('.//span').text,
        'status': doc.find('.//h1').find('.//span[@class="npo-status"]').text,
        'officers': []
    }
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
    for li in doc.findall(off_div):
        s = li.find('.//strong')
        a = s.find('./a')
        officer = {
            'role': clean_space(s.text).replace(' :', ''),
            'source_url': url,
            'officer_id': urljoin(url, a.get('href')),
            'name': clean_space(a.text)
        }
        data['officers'].append(officer)

    with lock:
        for officer in data.pop('officers'):
            roles.upsert(officer, ['source_url', 'officer_id'])
        orgs.upsert(data, ['source_url'])
        print data['name']
        #pprint(data)


def exc_scrape_npo(url):
    try:
        scrape_npo(url)
    except Exception, e:
        log.exception(e)


def scrape_npos():
    threaded(make_urls(), exc_scrape_npo, num_threads=10)

if __name__ == '__main__':
    scrape_npos()
