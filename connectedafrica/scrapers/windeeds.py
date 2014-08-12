import os
import requests
from pprint import pprint
from itertools import count
from urlparse import urljoin

import dataset
from scrapekit import Scraper
from scrapekit.util import collapse_whitespace

URL = 'https://www.windeedsearch.co.za/'
scraper = Scraper('windeeds', config={'threads': 4})
db_file = os.path.join(scraper.config.data_path, 'windeeds.db')
db = dataset.connect('sqlite:///%s' % db_file)
table_directors = db['directors']
table_companies = db['companies']


def documentcloudify(file_name, data):
    pass


def download_pdf(session, data):
    key = data.get('DbKey')
    file_name = 'windeeds_' + str(key) + '.pdf'
    file_name = os.path.join(scraper.config.data_path, 'cipc_pdfs', file_name)
    if not os.path.exists(file_name):
        dir_name = os.path.dirname(file_name)
        if not os.path.isdir(dir_name):
            os.makedirs(dir_name)
        url = urljoin(URL, '/Cipc/OtherPrintout/%s?format=Pdf' % key)
        res = session.get(url)
        with open(file_name, 'wb') as fh:
            fh.write(res.content)
    return file_name


@scraper.task
def init_session():
    url = urljoin(URL, '/Account/LoginByEmailPartial')
    params = {
        'GetCampaigns': 'True',
        'EmailIntegrationMode': 'False',
        'EmailAddress': 'ksharife@gmail.com',
        'Password': 'burtks',
        'RememberMe': 'true',
        'submitemail': 'Log%20In',
    }
    session = scraper.Session()
    res = session.get(url, params=params)
    assert res.json().get('success'), res.json()
    all_results.queue(session)


@scraper.task
def all_results(session):
    url = urljoin(URL, '/Client/AllResultsList')
    for page_no in count(1):
        params = {
            'SortOrder': 'Descending',
            'ColumnToSortBy': 'SearchDate',
            'firstLoad': 'true',
            'dateFilter': '5',
            'userScope': '0',
            'ResultCategoryFilter': '0',
            '_search': 'false',
            'nd': '1407843168396',
            'rows': '50',
            'page': page_no,
            'sidx': 'SearchDate',
            'sord': 'desc'
        }
        res = session.post(url, params)
        data = res.json()
        for row in data.get('Data'):
            scrape_result.queue(session, row)

        if page_no >= data.get('Total'):
            break


@scraper.task
def scrape_result(session, data):
    url = urljoin(URL, data.get('SearchAction'))
    if 'Cipc' not in url:
        return
    data['url'] = url
    data['pdf'] = download_pdf(session, data)
    if 'DirectorResult' in url:
        director_details(session, data)
    if 'CompanyResult' in url:
        company_details(session, data)


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
                if value and len(value) and value != '-':
                    if prefix:
                        label = '%s %s' % (prefix, label)
                    data[label] = value
                label = None
    return data


@scraper.task
def director_details(session, data):
    doc = session.get(data['url']).html()
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
        scraper.log.info("Director's details: %s" % company_name)
        table_directors.upsert(data, ['company_regno', 'url', 'CIPC ID'])
        #pprint(data)


@scraper.task
def company_details(session, data):
    doc = session.get(data['url']).html()
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
        scraper.log.info("Company details: %s" % data['director_name'])
        data.update(box_to_kv(block, prefix="CIPC-Person"))
        table_companies.upsert(data, ['CIPC-Company Registration number', 'url', 'director_name'])
        #pprint(data)


if __name__ == '__main__':
    init_session.run()
    dataset.freeze(table_companies, format='csv',
                   prefix=scraper.config.data_path,
                   filename='windeeds_cipc_companies.csv')
    dataset.freeze(table_directors, format='csv',
                   prefix=scraper.config.data_path,
                   filename='windeeds_cipc_directors.csv')
    scraper.report()