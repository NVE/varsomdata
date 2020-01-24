# -*- coding: utf-8 -*-
"""Methods for cleaning up encoding issues. Eg if there is trouble with encoding, file names or unix datetime
is used, methods are put here."""

import datetime as dt

__author__ = 'ragnarekker'


def unix_time_2_normal(unix_date_time):
    """Takes in a date in unix datetime and returns a "normal date"

    :param unix_date_time:    Unix date time in milliseconds from 1.1.1970
    :return:                The date as datetime object

    Ex: date = unix_time_2_normal(int(p['DtObsTime'][6:-2]))
    """

    # odata returns a string with prefix "Date". Cropp and cast.
    if "Date" in unix_date_time:
        unix_date_time = int(unix_date_time[6:-2])

    unix_datetime_in_seconds = unix_date_time/1000 # For some reason they are given in miliseconds
    date = dt.datetime.fromtimestamp(int(unix_datetime_in_seconds))
    return date


def remove_norwegian_letters(name_inn):
    """

    :param name_inn:
    :return name:
    """

    if name_inn is None:
        return None

    name = name_inn

    # Nordic chars
    if u'å' in name:
        name = name.replace(u'å', 'aa')
    if u'ø' in name:
        name = name.replace(u'ø', 'oe')
    if u'æ' in name:
        name = name.replace(u'æ', 'ae')
    if u'Å' in name:
        name = name.replace(u'Å', 'AA')
    if u'Ø' in name:
        name = name.replace(u'Ø', 'OE')
    if u'Æ' in name:
        name = name.replace(u'Æ', 'AE')

    # And one causing trouble on Svalbard
    if u'ö' in name:
        name = name.replace(u'ö', 'o')
    if u'Ö' in name:
        name = name.replace(u'Ö', 'O')

    # And the Sami chars
    if u'á' in name:
        name = name.replace(u'á', 'a')
    if u'Á' in name:
        name = name.replace(u'Á', 'A')
    if u'č' in name:
        name = name.replace(u'č', 'c')
    if u'Č' in name:
        name = name.replace(u'Č', 'C')
    if u'đ' in name:
        name = name.replace(u'đ', 'd')
    if u'Đ' in name:
        name = name.replace(u'Đ', 'D')
    if u'ŋ' in name:
        name = name.replace(u'ŋ', 'n')
    if u'Ŋ' in name:
        name = name.replace(u'Ŋ', 'N')
    if u'š' in name:
        name = name.replace(u'š', 's')
    if u'Š' in name:
        name = name.replace(u'Š', 'S')
    if u'ŧ' in name:
        name = name.replace(u'ŧ', 't')
    if u'Ŧ' in name:
        name = name.replace(u'Ŧ', 'T')
    if u'ž' in name:
        name = name.replace(u'ž', 'z')
    if u'Ž' in name:
        name = name.replace(u'Ž', 'Z')

    # name = name.encode('ascii', 'ignore')
    name = name.strip()                 # removes whitespace to left and right
    name = name.replace('\n', '')
    name = name.replace('\t', '')

    return name


def add_norwegian_letters(name_inn, use_encoding='utf8'):
    """

    :param name_inn:
    :return:
    """

    if name_inn is None:
        return None

    name = name_inn.decode(use_encoding, 'ignore')

    if u'ae' in name:
        name = name.replace(u'ae', 'æ'.decode(use_encoding, 'ignore'))
    if u'oe' in name:
        name = name.replace(u'oe', 'ø'.decode(use_encoding, 'ignore'))
    if u'aa' in name:
        name = name.replace(u'aa', 'å'.decode(use_encoding, 'ignore'))
    if u'AE' in name:
        name = name.replace(u'AE', 'Æ'.decode(use_encoding, 'ignore'))
    if u'OE' in name:
        name = name.replace(u'OE', 'Ø'.decode(use_encoding, 'ignore'))
    if u'AA' in name:
        name = name.replace(u'AA', 'Å'.decode(use_encoding, 'ignore'))

    return name


def make_standard_file_name(name_inn):
    """Remove all letters that may cause trouble in a filename

    :param name_inn: [String]
    :return:         [String]
    """

    name = name_inn.replace(",","").replace("/","").replace("\"", "")
    name = remove_norwegian_letters(name)

    return name


def text_cleanup(str_inn):
    """Method cleans up text.

    :param str_inn:
    :return str_inn:
    """

    if str_inn:
        str_inn = str_inn.rstrip()

        str_inn = str_inn.replace('\n', '')
        str_inn = str_inn.replace('\t', '')
        str_inn = str_inn.replace('<br/><br/>', ' ')

        str_inn = str_inn.replace('    ', ' ')  # in case four spaces occur by mistake
        str_inn = str_inn.replace('   ', ' ')
        str_inn = str_inn.replace('  ', ' ')  # in case double spaces occur by mistake
        str_inn = str_inn.replace(' - ', '-')
        str_inn = str_inn.replace(' -', '-')
        str_inn = str_inn.replace('- ', '-')

        # add space behind a comma if missing
        if ',' in str_inn:
            split_message = str_inn.split(',')
            str_inn = []
            for s in split_message:
                str_inn.append(s.strip())
            str_inn = ', '.join(str_inn)

        if '.' in str_inn:
            split_message = str_inn.split('.')
            str_inn = []
            for s in split_message:
                str_inn.append(s.strip())
            str_inn = '. '.join(str_inn)

        # remove spaces to left and right
            str_inn = str_inn.strip()

        # if there is no punctuation or exclamation on the end, add..
        if not (str_inn.endswith('.') or str_inn.endswith('!')):
            str_inn = str_inn + '.'

    return str_inn


def make_str(s):
    """Casts the input to string. If a string instance is Not given, Ikke gitt or None, return empty string."""

    if s == 'Not given':
        return ''
    if s == 'Ikke gitt':
        return ''
    if s is None:
        return ''
    return str(s)


if __name__ == "__main__":

    a = u'æøå'.encode('utf8')
    c = add_norwegian_letters('Proeve.')
    b = 1
