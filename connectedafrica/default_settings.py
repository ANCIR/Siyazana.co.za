import os

DEBUG = True
ASSETS_DEBUG = True

FLATPAGES_ROOT = '../pages/siyazana'
FLATPAGES_EXTENSION = '.md'

CACHE_TYPE = 'simple'

APP_NAME = 'Siyazana'
APP_SLOGAN = 'We know each other'

# Force HTTPS here:
PREFERRED_URL_SCHEME = os.getenv('GRANO_URL_SCHEME', 'http')

GRANO_HOST = os.environ.get('GRANO_HOST', 'http://beta.grano.cc/')
GRANO_APIKEY = os.environ.get('GRANO_APIKEY')
GRANO_PROJECT = os.environ.get('GRANO_PROJECT', 'southafrica')

WINDEEDS_USER = os.environ.get('WINDEEDS_USER')
WINDEEDS_PASS = os.environ.get('WINDEEDS_PASS')

# must use https for authorized requests
DOCCLOUD_HOST = os.environ.get('DOCCLOUD_HOST',
                               'https://sourceafrica.net/')
DOCCLOUD_USER = os.environ.get('DOCCLOUD_USER')
DOCCLOUD_PASS = os.environ.get('DOCCLOUD_PASS')
DOCCLOUD_PROJECT = os.environ.get('DOCCLOUD_PROJECT',
                                  'connectedAfrica')
DOCCLOUD_PROJECTID = int(os.environ.get('DOCCLOUD_PROJECTID', '130'))

SOURCE_NAMES = {
    'za-new-import.popit.mysociety.org': "People's Assembly",
    'www.windeedsearch.co.za': "Windeed CIPC",
    'www.jse.co.za': "JSE"
}
