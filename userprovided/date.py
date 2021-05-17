#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Checking and normalizing dates for the userprovided library
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
(c) 2020-2021 Rüdiger Voigt
Released under the Apache License 2.0
"""


import datetime
import logging
import re


def date_exists(year: int,
                month: int,
                day: int) -> bool:
    """Check if a date given by three integers is valid
       i.e exists in the calendar. """
    try:
        # int() will convert something like '01' to 1
        year = int(year)
        month = int(month)
        day = int(day)
    except ValueError:
        logging.error('Could not convert date parts to integer.')
        return False

    try:
        datetime.datetime(year, month, day)
    except ValueError:
        logging.error('Provided date does not exist in the calendar.')
        return False
    return True


def date_en_long_to_iso(date_string: str) -> str:
    """ Take a long format English date and return a standardized date string
       (i.e. YYYY-MM-DD). """
    date_string = date_string.strip()
    regex_long_date_en = re.compile(
        r"(?P<monthL>[a-zA-Z\.]{3,9})\s+(?P<day>\d{1,2})(th)?,\s*(?P<year>\d\d\d\d)")
    try:
        match = re.search(regex_long_date_en, date_string)
        if match:
            match_year = match.group('year')
            match_month = match.group('monthL')
            match_day = match.group('day')
        else:
            raise AttributeError('No date provided')
    except AttributeError:
        logging.error('Malformed date')
        raise

    # add a zero to day if <10
    if len(match_day) == 1:
        match_day = '0' + match_day
    months = {
        'January': '01', 'Jan.': '01',
        'February': '02', 'Feb.': '02',
        'March': '03', 'Mar.': '03',
        'April': '04', 'Apr.': '04',
        'May': '05',
        'June': '06', 'Jun.': '06',
        'July': '07', 'Jul.': '07',
        'August': '08', 'Aug.': '08',
        'September': '09', 'Sep.': '09',
        'October': '10', 'Oct.': '10',
        'November': '11', 'Nov.': '11',
        'December': '12', 'Dec.': '12'
        }
    try:
        match_month = months[str(match_month).lower().capitalize()]
    except KeyError:
        # String for month matched the regular expression but is no
        # recognized month.
        logging.error('Do not recognize month.')
        raise

    if not date_exists(int(match_year), int(match_month), int(match_day)):
        raise ValueError('Provided date is invalid.')

    return f"{match_year}-{match_month}-{match_day}"


def date_de_long_to_iso(date_string: str) -> str:
    """Take a long format German date and return a standardized date string
       (i.e. YYYY-MM-DD). """
    date_string = date_string.strip()
    regex_long_date_de = re.compile(
        r"(?P<day>\d{1,2})\.\s+(?P<monthL>[a-zA-Z\.]{3,9})\s+(?P<year>\d\d\d\d)")
    try:
        match = re.search(regex_long_date_de, date_string)
        if match:
            match_year = match.group('year')
            match_month = match.group('monthL')
            match_day = match.group('day')
        else:
            raise AttributeError('No date provided')
    except AttributeError:
        logging.exception('Malformed date')
        raise

    # add a zero to day if <10
    if len(match_day) == 1:
        match_day = '0' + match_day
    months = {
        'Januar': '01', 'Jan.': '01',
        'Februar': '02', 'Feb.': '02',
        'März': '03', 'Mar.': '03',
        'April': '04', 'Apr.': '04',
        'Mai': '05',
        'Juni': '06', 'Jun.': '06',
        'Juli': '07', 'Jul.': '07',
        'August': '08', 'Aug.': '08',
        'September': '09', 'Sep.': '09',
        'Oktober': '10', 'Okt.': '10',
        'November': '11', 'Nov.': '11',
        'Dezember': '12', 'Dez.': '12'
        }
    try:
        match_month = months[str(match_month).lower().capitalize()]
    except KeyError:
        # String for month matched the regular expression but is no
        # recognized month.
        logging.exception('Do not recognize month.')
        raise

    if not date_exists(int(match_year), int(match_month), int(match_day)):
        raise ValueError('Provided date is invalid.')

    return f"{match_year}-{match_month}-{match_day}"
