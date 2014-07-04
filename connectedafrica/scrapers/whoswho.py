import re, sys
from datetime import datetime
import urlparse

from lxml import html
import requests

from connectedafrica.scrapers.util import ScraperException


ENDPOINT_URL = 'http://whoswho.co.za/'
DATE_FORMAT = '%d-%m-%Y'
R_YEAR_RANGE = re.compile(
    r'(?P<start_m>[a-zA-Z]+)?(\s+)?(?P<start>\d{4})(\s+-\s+' \
    '((?P<current>present)|((?P<end_m>[a-zA-Z]+)?(\s+)?(?P<end>\d{4}))))?$'
)


# TODO: thread scraping


class ScraperException(Exception):
    pass


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


def scrape(url, degrees=0, scraped_urls=None):
    sys.stderr.write('Scraping %s\n' % url)

    if scraped_urls is None:
        scraped_urls = set()

    abs_url = get_absolute_url(url)
    if abs_url in scraped_urls:
        return
    data = get_data(abs_url)
    scraped_urls.add(abs_url)
    yield data

    if degrees > 0:
        for related_profile in data['related_profiles']:
            for data in scrape(related_profile['url'],
                               degrees - 1, scraped_urls):
                yield data


def get_data(abs_url):
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
    name_short = basic_el.xpath("*[@itemprop='name'][1]/text()")[0].strip()
    name_full = basic_el.xpath("*[@itemprop='name']/following-sibling::p[1]/em/text()")[0].strip()
    job_title = basic_el.xpath("*[@itemprop='jobTitle'][1]/text()")[0].strip()
    bio = basic_el.xpath("*[@id='contact_info']/preceding-sibling::p[1]/text()")[0].strip()
    data['basic_info'] = {
        'name_short': name_short,
        'name_full': name_full,
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
            elif el.tag == 'div' and current is not None:
                role_parts = [s.strip() for s in 
                              el.xpath('h6/br/preceding-sibling::text()[1]')[0]
                                .split('|')
                              if s.strip() != '']
                date_parts = [s.strip() for s in 
                              el.xpath('h6/br/following-sibling::text()[1]')[0]
                                .split('|')
                              if s.strip() != '']
                role_data = {
                    'role_name': role_parts[0],
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
                date_parts = el.xpath('p[1]/text()')[0].split('|')[-1].strip()
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
                            role_data['status'] = 'in progress'
                        elif date_parts.group('end'):
                            role_data['status'] = 'complete'
                            role_data['year_awarded'] = int(date_parts.group('end'))
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


if __name__ == '__main__':
    import json

    class DatetimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.strftime(DATE_FORMAT)
            return json.JSONEncoder.default(self, obj)

    url = lookup('Jacob Zuma')
    sys.stdout.write('[\n')
    generator = scrape(url, 1)
    data = next(generator)
    sys.stdout.write(json.dumps(data, indent=4, cls=DatetimeEncoder))
    for data in generator:
        sys.stdout.write(',\n')
        sys.stdout.write(json.dumps(data, indent=4, cls=DatetimeEncoder))
    sys.stdout.write('\n]')
