import os

DEBUG = True
ASSETS_DEBUG = False

FLATPAGES_ROOT = '../pages'
FLATPAGES_EXTENSION = '.md'


APP_NAME = 'connectedAFRICA'

GRANO_HOST = os.environ.get('GRANO_HOST', 'http://beta.grano.cc/')
GRANO_APIKEY = os.environ.get('GRANO_APIKEY')
GRANO_PROJECT = os.environ.get('GRANO_PROJECT', 'southafrica')
