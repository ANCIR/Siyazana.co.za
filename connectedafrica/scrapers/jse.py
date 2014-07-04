#
# Scrape the Johannesburg Stock Exchange Listed Companies.
#
# This scraper runs against a JSON interface provided by JSE and retrieve
# data related to all listed companies; the companies related to them
# (their Auditors, Sponsors etc.); and contact persons for some of them.
#

from pprint import pprint
import logging
import json

from thready import threaded
import requests

from connectedafrica.scrapers.util import MultiCSV


log = logging.getLogger('jse')

INDEX = 'https://www.jse.co.za/_vti_bin/JSE/CustomerRoleService.svc/GetAllIssuers'
ISSUER = 'https://www.jse.co.za/_vti_bin/JSE/CustomerRoleService.svc/GetIssuer'
BUSINESS = 'https://www.jse.co.za/_vti_bin/JSE/CustomerRoleService.svc/GetIssuerNatureOfBusiness'
ASSOCIATED = 'https://www.jse.co.za/_vti_bin/JSE/CustomerRoleService.svc/GetIssuerAssociatedRoles'
SOURCE_URL = 'https://www.jse.co.za/current-companies/listed-companies/issuer-profile?issuermasterid=%s'


def http_get(url, master_id):
    try:
        req = {
            'data': json.dumps({'issuerMasterId': master_id}),
            'headers': {'Content-Type': 'application/json'}
        }
        res = requests.post(url, **req)
        return res.json()
    except Exception:
        log.error("Failed to load: %s", SOURCE_URL % master_id)
        return {}


def scrape_record(csv, i):
    """ Scrape data regarding a single listed company. """
    record = http_get(ISSUER, i).get('GetIssuerResult')
    if not record.get('LongName'):
        return
    log.info('Scraping: %s', record.get('LongName'))

    nob = http_get(BUSINESS, i).get('GetIssuerNatureOfBusinessResult')
    record['NatureOfBusiness'] = nob

    res = http_get(ASSOCIATED, i)
    assocs = res.get('GetIssuerAssociatedRolesResult', [])

    record['source_url'] = SOURCE_URL % i
    record.pop('Contacts', None)
    csv.write('jse_entities.csv', record)

    for assoc in assocs:
        assoc.pop('Contacts', None)
        assoc['source_url'] = record['source_url']
        csv.write('jse_entities.csv', assoc)

        link = {
            'SourceName': assoc.get('LongName'),
            'TargetName': record.get('LongName'),
            'Role': assoc.get('RoleDescription'),
            'source_url': record['source_url']
        }
        csv.write('jse_links.csv', link)


def scrape_index():
    """ Get a list of listed companies. """
    req = {
        'data': json.dumps({}),
        'headers': {'Content-Type': 'application/json'}
    }
    res = requests.post(INDEX, **req)
    for row in res.json():
        yield str(row.get('MasterID'))


def scrape():
    csv = MultiCSV()
    threaded(scrape_index(), lambda i: scrape_record(csv, i),
             num_threads=30)
    csv.close()


if __name__ == '__main__':
    scrape()
