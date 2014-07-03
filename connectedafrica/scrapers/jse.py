#
# Scrape the Johannesburg Stock Exchange Listed Companies.
#
# This scraper runs against a JSON interface provided by JSE and retrieve
# data related to all listed companies; the companies related to them
# (their Auditors, Sponsors etc.); and contact persons for some of them.
#

import logging
import json

from thready import threaded
import requests

from connectedafrica.scrapers.util import write_json, read_json


log = logging.getLogger(__name__)

INDEX = 'https://www.jse.co.za/_vti_bin/JSE/CustomerRoleService.svc/GetAllIssuers'
ISSUER = 'https://www.jse.co.za/_vti_bin/JSE/CustomerRoleService.svc/GetIssuer'
BUSINESS = 'https://www.jse.co.za/_vti_bin/JSE/CustomerRoleService.svc/GetIssuerNatureOfBusiness'
ASSOCIATED = 'https://www.jse.co.za/_vti_bin/JSE/CustomerRoleService.svc/GetIssuerAssociatedRoles'
SENS = 'https://www.jse.co.za/_vti_bin/JSE/SENSService.svc/GetSensAnnouncementsByIssuerMasterId'
SOURCE_URL = 'https://www.jse.co.za/current-companies/listed-companies/issuer-profile?issuermasterid=%s'


def scrape_record(records, i):
    """ Scrape data regarding a single listed company. """
    req = {
        'data': json.dumps({'issuerMasterId': i}),
        'headers': {'Content-Type': 'application/json'}
    }
    res = requests.post(ISSUER, **req)
    if res.status_code != 200 or res.json().get('GetIssuerResult') is None:
        return

    record = res.json().get('GetIssuerResult')
    log.info('Scraping: %s', record.get('LongName'))

    try:
        res = requests.post(BUSINESS, **req)
        res = res.json()
        record['NatureOfBusiness'] = res.get('GetIssuerNatureOfBusinessResult')
    except Exception, e:
        log.exception(e)

    res = requests.post(ASSOCIATED, **req)
    res = res.json()
    record['AssociatedRoles'] = res.get('GetIssuerAssociatedRolesResult')

    record['source_url'] = SOURCE_URL % i
    records[i] = record


def scrape_index(records):
    """ Get a list of listed companies. """
    req = {
        'data': json.dumps({}),
        'headers': {'Content-Type': 'application/json'}
    }
    res = requests.post(INDEX, **req)
    for row in res.json():
        master_id = str(row.get('MasterID'))
        if master_id not in records:
            yield master_id


def scrape():
    records = read_json('jse.json') or {}
    threaded(scrape_index(records),
             lambda i: scrape_record(records, i),
             num_threads=30)
    write_json('jse.json', records)


if __name__ == '__main__':
    scrape()
