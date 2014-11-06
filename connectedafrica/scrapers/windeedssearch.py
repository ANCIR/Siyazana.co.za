import re

from scrapekit.tasks import Task

from connectedafrica.scrapers import windeeds
from connectedafrica.scrapers.util import MultiCSV


class SearchedPerson(object):
    description_re = re.compile(r'^(?P<name>.*),\s*(?P<id>\d+)$')

    def __init__(self, url, description):
        self.url = url
        self.description = description
        self.name = None
        self.national_id = None

        match = self.description_re.match(description)
        if match:
            self.name = match.group('name')
            self.national_id = match.group('id')

    def __hash__(self):
        return self.url.__hash__()

    def __repr__(self):
        return '<SearchedPerson(url="%s")>' % self.url


class Searcher(windeeds.ResultsScraper):

    def __init__(self, name='windeedssearch', config=None):
        super(Searcher, self).__init__(name, config)

        for fn_name in ():
            task = Task(self, getattr(self, fn_name))
            setattr(self, fn_name, task)

    def init_session(self, csv):
        self.searched_persons = set()
        session = self.Session()
        windeeds.login_session(session)
        # collect existing results before searching
        self.all_results.run(csv, session)

        for person in self.searched_persons:
            csv.write('windeeds/windeeds_persons.csv', person.__dict__)

    def scrape_result(self, csv, session, data):
        url = data.get('SearchAction')
        if 'Cipc' not in url:
            return
        if 'DirectorResult' not in url:
            return
        description = data.get('Description')
        self.searched_persons.add(SearchedPerson(
            url=url,
            description=description,
        ))


def scrape():
    searcher = Searcher()
    csv = MultiCSV()
    searcher.init_session.run(csv)
    csv.close()
    searcher.report()


if __name__ == '__main__':
    scrape()
