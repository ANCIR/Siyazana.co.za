import re, sys
from datetime import datetime
import threading
import urlparse

from lxml import html
import networkx as nx
import requests
from thready import threaded
import unicodecsv as csv

from connectedafrica.scrapers.util import (ScraperException, MultiCSV,
                                           set_to_empty, gdocs_persons)


ENDPOINT_URL = 'http://whoswho.co.za/'
DATE_FORMAT = '%d-%m-%Y'
R_YEAR_RANGE = re.compile(
    r'(?P<start_m>[a-zA-Z]+)?(\s+)?(?P<start>\d{4})(\s+-\s+' \
    '((?P<current>present)|((?P<end_m>[a-zA-Z]+)?(\s+)?(?P<end>\d{4}))))?$'
)


class ProfileNotFound(ScraperException):
    pass


def lookup(search_term):
    response = requests.get('%ssearch/site/%s' % (ENDPOINT_URL, search_term))
    response.raise_for_status()
    root = html.fromstring(response.content)
    result_el = root.find_class('searchResult')
    if not result_el:
        raise ProfileNotFound("Profile page for search term '%s' not found"
                              % search_term)
    result_el = result_el[0]
    url = result_el.xpath('a[1]/@href')[0]
    return url


def get_data(url):
    abs_url = get_absolute_url(url)
    response = requests.get(abs_url)
    response.raise_for_status()
    data = parse_content(response.text)
    data['url'] = abs_url
    return data


def get_absolute_url(url):
    if not url.startswith(ENDPOINT_URL):
        parts = urlparse.urlparse(url)
        if parts.scheme == 'https':
            raise ScraperException("Who's Who does not accept https connections")
        elif parts.netloc:
            raise ScraperException("'%s' is not a Who's Who URL" % url)
        return urlparse.urlunparse(['http', 'whoswho.co.za'] + list(parts[2:]))
    return url


def first_or_empty(xpath_list):
    if len(xpath_list) > 0:
        return xpath_list[0].strip()
    return ''


def parse_content(content):
    # TODO: achievements sections
    data = {
        'related_profiles': [],
        'professional_details': [],
        'activities': [],
        'education': [],
    }
    root = html.fromstring(content)

    # basic info
    basic_el = root.xpath("//*[@itemtype='http://schema.org/Person'][1]")
    if len(basic_el) == 0:
        raise ScraperException("Content doesn't appear to be a person's profile")
    basic_el = basic_el[0]
    display_name = first_or_empty(basic_el.xpath("*[@itemprop='name'][1]/text()"))
    full_name = first_or_empty(basic_el.xpath("*[@itemprop='name']/following-sibling::p[1]/em/text()"))
    job_title = first_or_empty(basic_el.xpath("*[@itemprop='jobTitle'][1]/text()"))
    bio = first_or_empty(basic_el.xpath("*[@id='contact_info']/preceding-sibling::p[1]/text()"))
    data['basic_info'] = {
        'display_name': display_name,
        'full_name': full_name,
        'job_title': job_title,
        'bio': bio
    }
    # date of birth
    birth_node = basic_el.xpath("p[contains(., 'Born')][1]")
    if birth_node:
        birth_node = birth_node[0]
        birth_date = birth_node.xpath('a[1]/text()')
        if birth_date:
            data['basic_info']['birth_date'] = datetime.strptime(
                birth_date[0],
                DATE_FORMAT
            )
        birth_town = birth_node.find_class('locality')
        if birth_town:
            if birth_town[0].xpath('a'):
                data['basic_info']['birth_town'] = birth_town[0].xpath('a[1]/text()')[0]
            elif birth_town[0].text:
                text = birth_town[0].text.strip()
                if text.startswith('in '):
                    text = text[3:]
                data['basic_info']['birth_town'] = text
        birth_country = birth_node.xpath("*[@itemprop='nationality'][1]/text()")
        if birth_country:
            data['basic_info']['country'] = birth_country[0]

    # professional info
    prof_el = root.get_element_by_id('professional-details', None)
    if prof_el is not None:
        current = None
        for el in prof_el:
            if el.tag == 'h2':
                if current is None:
                    current = True
                else:
                    current = False
            elif el.tag == 'div' and current is not None and \
                    not el.get('class', ''):
                role_parts = [s.strip() for s in 
                              el.xpath('h6/br/preceding-sibling::text()[1]')[0]
                                .split('|')
                              if s.strip() != '']
                date_parts = [s.strip() for s in 
                              el.xpath('h6/br/following-sibling::text()[1]')[0]
                                .split('|')
                              if s.strip() != '']
                role_data = {
                    'role_name': first_or_empty(role_parts),
                    'status': 'active' if current else 'inactive'
                }
                # get start and end year
                if date_parts:
                    date_parts = R_YEAR_RANGE.match(date_parts[-1])
                    if date_parts:
                        role_data['role_start_year'] = int(date_parts.group('start'))
                        if date_parts.group('current'):
                            assert current
                        elif date_parts.group('end'):
                            role_data['role_end_year'] = int(date_parts.group('end'))
                        elif not current:
                            role_data['role_end_year'] = role_data['role_start_year']
                # get organization info
                org_el = el.xpath('h6/a[last()]')
                if len(org_el) > 0:
                    org_el = org_el[0]
                    role_data['organization_name'] = org_el.text
                    role_data['organization_url'] = org_el.get('href', None)
                    if role_data['organization_url']:
                        role_data['organization_url'] = '%s%s' % (
                            ENDPOINT_URL.rstrip('/'),
                            role_data['organization_url']
                        )
                # the organization doesn't have a url
                # use 2nd last piece of plain text
                elif len(role_parts) > 2:
                    role_data['organization_name'] = role_parts[-2]
                else:
                    continue
                data['professional_details'].append(role_data)

    # education info
    edu_el = root.get_element_by_id('education', None)
    if edu_el is not None:
        level = None
        for el in edu_el.xpath("h1[1]/following-sibling::node()"):
            if not isinstance(el, html.HtmlElement):
                continue
            if el.tag == 'h2':
                level = el.text.lower()
                continue
            elif el.tag != 'div' or el.get('class', None) == 'clear':
                continue
            # parse secondary education (single line)
            if level == 'secondary':
                org_parts = el.xpath('h6[1]/text()')[0]
                org_parts = [s.strip() for s in org_parts.split(',')]
                place = ', '.join(org_parts[1:])
                edu_data = {
                    'organization_name': org_parts[0],
                    'level': level,
                    'place': place,
                }
                match = re.match(r'.*(?P<year>\d{4})$', place)
                if match:
                    edu_data['year_awarded'] = int(match.group('year'))
                    edu_data['status'] = 'complete'
                    edu_data['place'] = place[:-7]
            # parse tertiary education (complex tags)
            elif level == 'tertiary':
                edu_data = {'level': level}
                org_name = el.xpath('h6[1]/a')
                if org_name:
                    edu_data['organization_name'] = org_name[0].text
                else:
                    org_name = el.xpath('h6[1]/text()')
                    if org_name:
                        edu_data['organization_name'] = org_name[0]
                try:
                    date_parts = el.xpath('p[1]/text()')[0] \
                                   .split('|')[-1] \
                                   .strip()
                except IndexError:
                    continue
                if date_parts.startswith('Awarded in ') or \
                        date_parts.startswith('Completed '):
                    edu_data['year_awarded'] = int(date_parts[-4:])
                    if date_parts.startswith('Completed '):
                        edu_data['status'] = 'complete'
                    qualification = el.xpath('p[2]/text()')
                    if qualification:
                        edu_data['qualification'] = qualification[0]
                else:
                    date_parts = R_YEAR_RANGE.match(date_parts)
                    if date_parts:
                        qualification = el.xpath('p[2]/text()')
                        if qualification:
                            edu_data['qualification'] = qualification[0]
                        edu_data['start_year'] = int(date_parts.group('start'))
                        if date_parts.group('current'):
                            edu_data['status'] = 'in progress'
                        elif date_parts.group('end'):
                            edu_data['status'] = 'complete'
                            edu_data['year_awarded'] = int(date_parts.group('end'))
                    else:
                        edu_data['qualification'] = date_parts
            data['education'].append(edu_data)

    # activities info
    activity_el = root.get_element_by_id('activities', None)
    if activity_el is not None:
        # only doing memberships
        for el in activity_el.xpath("h2[.='Memberships']/following-sibling::node()"):
            if not isinstance(el, html.HtmlElement):
                continue
            if el.tag != 'div' or el.get('class', None) == 'clear':
                break
            org_name = el.xpath('h6[1]/text()')[0]
            role_data = {'organization_name': org_name}
            role_parts = el.xpath('p[1]/em')[0].text
            if role_parts:
                role_parts = role_parts.split(',')
                role_data['role_name'] = role_parts[0].strip()
                if len(role_parts) == 2:
                    date_parts = R_YEAR_RANGE.match(role_parts[1].strip())
                    if date_parts:
                        role_data['role_start_year'] = int(date_parts.group('start'))
                        if date_parts.group('current'):
                            role_data['status'] = 'active'
                        elif date_parts.group('end'):
                            role_data['status'] = 'inactive'
                            role_data['role_end_year'] = int(date_parts.group('end'))
            data['activities'].append(role_data)

    # related profile info
    related_el = root.get_element_by_id('related', None)
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


def write_to_csv(csv, data):
    # Person
    out_data = data['basic_info'].copy()
    out_data['source_url'] = data['url']
    set_to_empty(out_data, ('birth_date', 'birth_town', 'country'))
    csv.write('whoswho_persons.csv', out_data)
    person_name = out_data['display_name']  # don't have a full name for everyone
    # Memberships (professional)
    for details in data['professional_details']:
        out_data = details.copy()
        out_data['source_url'] = data['url']
        out_data['person_name'] = person_name
        set_to_empty(out_data, ('role_start_year', 'role_end_year',
                                'organization_name', 'organization_url'))
        csv.write('whoswho_memberships.csv', out_data)
    # Memberships (other)
    for details in data['activities']:
        out_data = details.copy()
        out_data['source_url'] = data['url']
        out_data['person_name'] = person_name
        set_to_empty(out_data, ('role_start_year', 'role_end_year',
                                'role_name', 'status'))
        csv.write('whoswho_memberships.csv', out_data)
    # Qualifications
    for details in data['education']:
        out_data = details.copy()
        out_data['source_url'] = data['url']
        out_data['person_name'] = person_name
        set_to_empty(out_data, ('organization_name', 'place',
                                'year_awarded', 'status',
                                'start_year', 'qualification'))
        csv.write('whoswho_qualifications.csv', out_data)


class NetworkScraper(object):
    '''
    This scraper scrapes related URLs and keeps track of their connectivity.
    Multiple scrape calls won't re-scrape a URL.
    '''

    def __init__(self, csv=None, out=sys.stdout, thread_count=5):
        self.url_graph = nx.DiGraph()
        self.url_scraped = set()
        self.thread_count = thread_count
        self.csv = csv
        self.out = out
        self.lock = threading.Condition()
        self.out_lock = threading.Lock()

    def scrape(self, search_term=None, start_url=None, degrees=0):
        if not (search_term or start_url):
            raise ValueError("Either search_term or start_url argument "
                             "is required.")
        start_url = start_url or lookup(search_term)
        shared_state = {'processed_urls': 0}

        if start_url in self.url_scraped:
            # we have scraped the current url, but we still need to
            # scrape all its descendants with degree <= degrees
            url_to_scrape = set()
            nodes = [(start_url, 0)]
            while len(nodes) > 0:
                url, degree = nodes.pop(0)
                if degree <= degrees and url not in self.url_scraped:
                    url_to_scrape.add(url)
                elif degree < degrees:
                    child_urls = self.url_graph[url].keys()
                    nodes.extend([(u, degree + 1) for u in child_urls])
        else:
            self.url_graph.add_node(start_url)
            url_to_scrape = set([start_url])

        def produce_urls(source_url, new_urls):
            with self.lock:
                self.url_graph.add_edges_from([(source_url, u) for u in new_urls])
                for url in new_urls:
                    if (url not in self.url_scraped and
                            url not in url_to_scrape and
                            len(nx.shortest_path(self.url_graph, start_url, url))
                            <= degrees + 1):
                        url_to_scrape.add(url)
                shared_state['processed_urls'] += 1
                self.lock.notify()

        def consume_urls():
            generated_urls = 0
            if len(url_to_scrape) == 0:
                return
            while True:
                with self.lock:
                    if len(url_to_scrape) == 0:
                        self.lock.wait()
                    if len(url_to_scrape) == 0:
                        if generated_urls == shared_state['processed_urls']:
                            raise StopIteration
                    else:
                        url = url_to_scrape.pop()
                        self.url_scraped.add(url)
                        generated_urls += 1
                        yield url

        def thread_func(url):
            with self.out_lock:
                sys.stderr.write('Scraping %s\n' % url)
            try:
                data = get_data(url)
                produce_urls(url, [d['url'] for d in data['related_profiles']])
            except:
                produce_urls(url, [])
                raise
            if self.csv is not None:
                write_to_csv(self.csv, data)
            else:
                with self.out_lock:
                    self.out.write('%r\n' % data)

        threaded(consume_urls(), thread_func, num_threads=self.thread_count)


if __name__ == '__main__':
    scraper = NetworkScraper(csv=MultiCSV(), thread_count=5)
    degrees = 0
    try:
        degrees = int(sys.argv[1])
    except (IndexError, ValueError):
        pass
    for data in gdocs_persons():
        try:
            scraper.scrape(
                search_term=data['Full Name'],
                start_url=data['WhosWho'],
                degrees=degrees
            )
        except ProfileNotFound as e:
            sys.stderr.write("%s\n" % str(e))
