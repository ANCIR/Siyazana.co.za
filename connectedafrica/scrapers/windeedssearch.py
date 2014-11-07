import re

from Levenshtein import jaro
from scrapekit.tasks import Task

from connectedafrica.scrapers import windeeds
from connectedafrica.scrapers.util import (MultiCSV, gdocs_persons,
                                           normalize_string)


class SearchedPerson(object):
    description_re = re.compile(
        ur'^(?P<last_name>.*),\s*(?P<first_name>.*),\s*(?P<id>\d+)$',
        flags=re.UNICODE
    )

    def __init__(self, url, description):
        self.url = url
        self.description = description
        self.national_id = None
        self.first_name = None
        self.last_name = None

        match = self.description_re.match(description)
        if match:
            self.national_id = match.group('id')
            self.first_name = match.group('first_name')
            self.last_name = match.group('last_name')

    def __hash__(self):
        return self.url.__hash__()

    def __repr__(self):
        return '<%s(name="%s %s")>' % \
                (self.__class__.__name__, self.first_name, self.last_name)


class SearchedPersonNotFound(SearchedPerson):

    def __init__(self, url, description):
        super(SearchedPersonNotFound, self).__init__(url, description)

        if not self.description_re.match(description):
            parts = description.split(', ')
            if re.match(ur'^\d+$', parts[-1]):
                self.national_id = parts[-1]
                names = parts[0:-1]
            else:
                names = parts
            if len(names) >= 2:
                self.first_name = ', '.join(names[1:])
            if len(names) >= 1:
                self.last_name = names[0]


persons = set()
persons_by_id = {}
persons_by_last_name = {}


def record_searchedperson(person):
    if person.national_id:
        persons_by_id[person.national_id] = person

    if person not in persons and person.last_name:
        last_name_norm = normalize_string(person.last_name)
        persons_by_last_name.setdefault(last_name_norm, [])
        persons_by_last_name[last_name_norm].append(person)

    persons.add(person)


def has_matching_word(phrase1, phrase2):
    for word1 in phrase1.split():
        for word2 in phrase2.split():
            if jaro(word1, word2) > 0.9:
                return True


def find_searchedperson(first_name, last_name, national_id):
    '''
    Try super hard to match this person up. Rather return bad
    match than no match - we can manually search bad matches.
    '''
    if national_id in persons_by_id:
        yield persons_by_id[national_id]

    last_name_norm = normalize_string(last_name)
    matches = []
    if last_name_norm in persons_by_last_name:
        matches = persons_by_last_name[last_name_norm]
    else:
        for key in persons_by_last_name.keys():
            if jaro(last_name_norm, key) > 0.9:
                matches.extend(persons_by_last_name[key])

    first_name_norm = normalize_string(first_name)
    for match in matches:
        key = normalize_string(match.first_name)
        '''
        A match is valid if:
        1. We don't have a first name because only last name
           was used in a failed search.
        2. The entire first name string is similar.
        3. One of the first names are similar.
        '''
        if (not key and isinstance(match, SearchedPersonNotFound)) \
                or jaro(first_name_norm, key) > 0.9 \
                or has_matching_word(first_name_norm, key):
            yield match


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

        for data in gdocs_persons():
            matches = list(find_searchedperson(
                data['First Name'],
                data['Last Name'],
                data['ID #']
            ))
            if matches:
                self.log.debug('%s matched %r' % (data['Full Name'], matches))
            else:
                self.log.debug('%s unmatched' % data['Full Name'])


    def scrape_result(self, csv, session, data):
        url = data.get('SearchAction')
        if 'Cipc' not in url:
            return
        if 'DirectorResult' in url:
            cls = SearchedPerson
        elif 'NoResult' in url and 'Director' in data.get('SearchType'):
            cls = SearchedPersonNotFound
        else:
            return
        description = data.get('Description').decode('utf8')
        record_searchedperson(cls(
            url=url,
            description=description,
        ))


def scrape():
    searcher = Searcher()
    csv = MultiCSV()
    searcher.init_session(csv)
    csv.close()
    searcher.report()


if __name__ == '__main__':
    scrape()
