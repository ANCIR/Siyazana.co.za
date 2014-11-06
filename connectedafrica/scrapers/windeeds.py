import os
from time import time
from itertools import count
from urlparse import urljoin

import requests
from scrapekit import Scraper
from scrapekit.tasks import Task
from scrapekit.util import collapse_whitespace

from connectedafrica.core import app
from connectedafrica.scrapers.util import MultiCSV, DATA_PATH


URL = 'https://www.windeedsearch.co.za/'


def documentcloudify(file_name, data):
    auth = (app.config.get('DOCCLOUD_USER'),
            app.config.get('DOCCLOUD_PASS'))
    host = app.config.get('DOCCLOUD_HOST')
    project_name = app.config.get('DOCCLOUD_PROJECT')
    project_id = app.config.get('DOCCLOUD_PROJECTID')
    title = data.get('Description')
    search_url = urljoin(host, '/api/search.json')
    params = {'q': 'project:"%s" title:"%s"' % (project_name, title)}
    res = requests.get(search_url, params=params, auth=auth,
                       verify=False)
    found = res.json()
    if found.get('total') > 0:
        return found.get('documents')[0].get('canonical_url')
    req_data = {
        'title': title,
        'source': 'Windeeds CIPC Search',
        'published_url': data.get('url'),
        'access': 'private',
        'project': project_id
        }
    files = {
        'file': open(file_name, 'rb')
    }
    upload_url = urljoin(host, '/api/upload.json')
    res = requests.post(upload_url, files=files,
                        verify=False, auth=auth, data=req_data)
    return res.json().get('canonical_url')


def download_pdf(session, data):
    key = data.get('DbKey')
    file_name = 'windeeds_' + str(key) + '.pdf'
    file_name = os.path.join(ResultsScraper.data_path, 'cipc_pdfs', file_name)
    if not os.path.exists(file_name):
        dir_name = os.path.dirname(file_name)
        try:
            os.makedirs(dir_name)
        except:
            pass
        url = urljoin(URL, '/Cipc/OtherPrintout/%s?format=Pdf' % key)
        res = session.get(url)
        with open(file_name, 'wb') as fh:
            fh.write(res.content)
    return documentcloudify(file_name, data)


def box_to_kv(block, prefix=None):
    data = {}
    for row in block.findall('./div[@class="result-section-row"]'):
        label = None
        for div in row.findall('./div'):
            clazz = div.get('class')
            if 'result-label' in clazz:
                label = collapse_whitespace(div.text_content())
            else:
                value = collapse_whitespace(div.text)
                if not len(value) or value == '-':
                    value = None
                if prefix:
                    label = '%s %s' % (prefix, label)
                data[label] = value
                label = None
    return data


def login_session(session):
    url = urljoin(URL, '/Account/LoginByEmailPartial')
    params = {
        'GetCampaigns': 'True',
        'EmailIntegrationMode': 'False',
        'EmailAddress': app.config.get('WINDEEDS_USER'),
        'Password': app.config.get('WINDEEDS_PASS'),
        'RememberMe': 'true',
        'submitemail': 'Log%20In',
    }
    res = session.get(url, params=params)
    assert res.json().get('success'), res.json()


class ResultsScraper(Scraper):
    data_path = DATA_PATH

    def __init__(self, name='windeeds', config=None):
        defaults = {
            'threads': 4,
            'data_path': self.data_path
        }
        if config is None:
            config = {}
        for key, val in defaults.iteritems():
            config.setdefault(key, val)

        super(ResultsScraper, self).__init__(name, config=config)
        # turn a bunch of methods into tasks
        for fn_name in ('init_session', 'all_results', 'scrape_result',
                        'director_details', 'company_details'):
            task = Task(self, getattr(self, fn_name))
            setattr(self, fn_name, task)

    def init_session(self, csv):
        session = self.Session()
        login_session(session)
        self.all_results.queue(csv, session)

    def all_results(self, csv, session):
        url = urljoin(URL, '/Client/AllResultsList')
        for page_no in count(1):
            params = {
                'SortOrder': 'Descending',
                'ColumnToSortBy': 'SearchDate',
                'firstLoad': 'false',
                'dateFilter': '4',
                'userScope': '1',
                'ResultCategoryFilter': '0',
                '_search': 'false',
                'nd': str(int(time() * 1000)),
                'rows': '50',
                'page': page_no,
                'sidx': 'SearchDate',
                'sord': 'desc'
            }
            res = session.post(url, params)
            data = res.json()
            for row in data.get('Data'):
                self.scrape_result.queue(csv, session, row)

            if page_no >= data.get('Total'):
                break

    def scrape_result(self, csv, session, data):
        url = urljoin(URL, data.get('SearchAction'))
        if 'Cipc' not in url:
            return
        data['url'] = url
        data['pdf'] = download_pdf(session, data)
        if 'DirectorResult' in url:
            self.director_details(csv, session, data)
        if 'CompanyResult' in url:
            self.company_details(csv, session, data)

    def director_details(self, csv, session, data):
        doc = session.get(data['url'], cache='force').html()
        for block in doc.findall('.//div[@class="result-section-block"]'):
            prof = block.find('./a[@rel="DirectorCompanyProfile"]')
            if prof is None:
                continue
            title = collapse_whitespace(block.findtext('./h4'))
            _, title = title.split('COMPANY:', 1)
            title, _ = title.rsplit('(', 1)
            title = map(collapse_whitespace, title.rsplit(', ', 1))
            company_name, company_regno = title
            data['company_name'] = company_name
            data['company_regno'] = company_regno
            data.update(box_to_kv(block, prefix="CIPC"))
            self.log.info("Director's details: %s" % company_name)
            csv.write('windeeds/windeeds_directors.csv', data)

    def company_details(self, csv, session, data):
        doc = session.get(data['url'], cache='force').html()
        for block in doc.findall('.//div[@class="result-block"]'):
            if block.find('./a[@name="CompanyInformation"]') is None:
                continue
            data.update(box_to_kv(block, prefix="CIPC-Company"))

        for block in doc.findall('.//div[@class="result-section-block"]'):
            prof = block.find('./a[@rel="Directors"]')
            if prof is None:
                continue
            title = collapse_whitespace(block.findtext('./h4'))
            title, _ = title.rsplit(' - ', 1)
            data['director_name'] = collapse_whitespace(title)
            self.log.info("Company details: %s" % data['director_name'])
            data.update(box_to_kv(block, prefix="CIPC-Person"))
            csv.write('windeeds/windeeds_companies.csv', data)


def scrape():
    scraper = ResultsScraper()
    csv = MultiCSV()
    scraper.init_session.run(csv)
    csv.close()
    scraper.report()


if __name__ == '__main__':
    scrape()
