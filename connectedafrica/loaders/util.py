from datetime import datetime


DEFAULT_DATE_FORMAT = '%m/%d/%Y'


def parse_date(datestr, dateformat=None):
    if dateformat is None:
        dateformat = DEFAULT_DATE_FORMAT
    try:
        return datetime.strptime(datestr, dateformat)
    except ValueError:
        return None
