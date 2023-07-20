import re

from datetime import datetime, date, MAXYEAR
from dateutil import parser
from typing import Tuple, List, Optional
from text2phenotype.common.log import operations_logger

MONTH_DAYS = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth',
              'seventh', 'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth',
              'thirteenth', 'fourteenth', 'fifteenth', 'sixteenth', 'seventeenth',
              'eighteenth', 'nineteenth', 'twentieth', 'twenty-first', 'twenty-second',
              'twenty-third', 'twenty-fourth', 'twenty-fifth', 'twenty-sixth',
              'twenty-seventh', 'twenty-ninth', 'twenty-eighth', 'thirtieth', 'thirty-first']


class CustomParseInfo(parser.parserinfo):
    def convertyear(self, year, century_specified=False):
        min_year = datetime.now().year - 2000 + 10
        # doing this comparison bc we are comparing against years that are 2 digits and we want to set all dates that
        # have a year anywhere less than 10 years in the future to be set to be in the current century
        # any year more than 10 years in the future is assumed to have belonged to the 19th century
        # no change  will occur for years already in the 4 digit format

        if min_year < year < 100:
            # All dates with two digits year between 25 and 100 are in the 20th century
            year += 1900
        if 0 <= year <= min_year:
            year += 2000
        return year


def _replace_number_words(text: str) -> str:
    """
    :param text: text expected to contain number words
    :return: text with number words replaced to digits
    """
    result = text
    for w in text.split():
        if w.lower() in MONTH_DAYS:
            result = result.replace(w, str(MONTH_DAYS.index(w.lower()) + 1), 1)
    return result


def parse_dates(text: str) -> List[Tuple[datetime, Tuple[int, int]]]:
    """ Given text expected to contain dates. Method parse dates from text using regex patterns
    and dateutil.pareser.

    :param text: The text to search for dates
    :return: tuple of python datetime object and tuple containing date position in text,
    or None if exception occurs.
    """
    try:
        m = r'(?:(?:1[012])|(?:0?[1-9]))'
        d = r'(?:(?:0?[1-9])|(?:3[01])|(?:[12]?[0-9])' \
            f'|(?:{"|".join(MONTH_DAYS)})' \
            r')'
        y = r'(?:[0-9]{2})'
        Y = r'(?:(?:19|20)[0-9]{2})'
        B = r'(?:(?:January|February|March|April|May|June|July|August|September|October|November|December)' \
            r'|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec))'

        pattern = r'(?<!\d)(' \
                  f'({m}[-/]{d}[-/]{Y})' \
                  f'|({m}[-/]{d}[-/]{y})' \
                  f'|({Y}[-/]{m}[-/]{d})' \
                  f'|({d}[-/\s]?{B}[-/\s]?{Y})' \
                  f'|({B}\s{d}(?:st|nd|rd|th)?[,.]?\s?{Y})' \
                  f'|({d}(\s?(?:st|nd|rd|th)\sof)?\s{B}[,.]?\s?{Y})' \
                  f'|({B}\s?{d})' \
                  f'|({B}(?:(?:\sof)|,)?\s?{Y})' \
                  f'|({d}\s?(?:st|nd|rd|th)?(?:(?:\sof)|,)?\s?{B})' \
                  f'|({m}/{Y})' \
                  f'|({m}/{y})' \
                  r')(?:\D|$)'

        parse_info = CustomParseInfo()

        # set it to max year so that it doesn't always convert to the earliest date
        # but eventually needs to get rid of randomly assigning a year to a month/day type
        default_date = datetime(MAXYEAR, 1, 1)

        matches = list()
        for m in re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE):
            if m:
                try:
                    # replace commas with ', ' due to weird unexpected behavior deep in the parser.parse
                    # function(timelex.split) interprets day,year as float = day.year
                    matches.append((
                        parser.parse(
                            _replace_number_words(m.group().replace(',', ', ')),
                            parse_info,
                            fuzzy=True,
                            default=default_date
                        ),
                        m.span()
                    ))
                except Exception as ex:
                    operations_logger.debug(ex)
        return matches

    except Exception as ex:
        operations_logger.debug(ex)
        return []


# TODO: needed for surrogate injection, reconcile this with the above
def parse_date_and_format(text: str) -> Optional[Tuple[date, str]]:
    """ Given text expected to contain a date, try reasonable methods of converting
    text to datetime.  Default format = mm/dd/YYYY
    Returns tuple of python datetime object and str pattern used for converting,
    or None if date cannot be ascertained from text.
    :param text: The text to search for dates
    :return: The first date found
    """
    try:
        patterns = [
            '%m/%d/%Y',
            '%m/%d/%y',
            '%m-%d-%Y',
            '%m-%d-%y',
            '%m/%Y',
            '%m/%y',
            '%B %d, %Y',
            '%B %d',
            '%B %Y',
            '%B of %Y',
            '%B, %Y',
            '%dst of %B',
            '%dnd of %B',
            '%drd of %B',
            '%dth of %B',
            '%Y-%m-%d',
            '%Y/%m/%d',  # 2118/07/04
            '%b %Y',  # Nov 2093
            '%b %d, %Y',  # Jun 10, 2079
            '%m %Y',  # 11 2074
            '%m.%d.%y',  # 10.25.78
            '%B %dth, %Y',  # September 28th, 2085
            '%d-%b-%Y',  # 28-Aug-2097
            '%A, %B %d, %Y',  # Tuesday, October 01, 2074
            '%d-%B-%Y',  # 25-March-2064
            '%B %d,%Y',  # March 25,2064
            '%b. %Y',  # Feb. 2068
            '%d%b%y',  # 30Aug71
            '%b. \'%y',  # Oct. '94
            '%b, %Y',  # Oct, 2079
            '%d %b %Y',  # 17 Aug 2133
            '%b %y',  # Nov 97
            '\'%y',  # '68
            '%b-%Y',  # Sep-2075
            '%d-%b-%y',  # 24-Jul-76
        ]

        for p in patterns:
            try:
                return datetime.strptime(text, p).date(), p
            except ValueError:
                pass

        return None

    except Exception as ex:
        operations_logger.debug(ex)
        return None
