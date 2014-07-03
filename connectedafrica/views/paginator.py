from flask import request

from connectedafrica.core import url_for


class Paginator(object):

    def __init__(self, results, wiggle=3):
        self.results = results
        self.wiggle = wiggle
        self.page = results.get('page')
        self.pages = results.get('pages')

    def show_pages(self):
        low = self.page - self.wiggle
        high = self.page + self.wiggle

        if low < 1:
            low = 1
            high = min((2*self.wiggle)+1, self.pages)

        if high > self.pages:
            high = self.pages
            low = max(1, self.pages - (2*self.wiggle)+1)
        return range(low, high+1)

    @property
    def links(self):
        for page in self.show_pages():
            args = dict(request.args.items())
            args['offset'] = (page - 1) * self.results.get('limit')
            yield (page, url_for(request.endpoint, **args))
