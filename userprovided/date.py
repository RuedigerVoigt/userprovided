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
    """Validates if a date exists in the calendar.

    Checks whether the given year, month, and day combination represents
    a valid date, including leap year considerations.

    Args:
        year: The year as an integer.
        month: The month as an integer (1-12).
        day: The day as an integer (1-31).

    Returns:
        True if the date exists in the calendar, False otherwise.
    """
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
    """Converts long-format English dates to ISO format (YYYY-MM-DD).

    Parses English date strings in formats like "July 4, 1776" or
    "May 8th, 1945" and converts them to ISO 8601 date format.

    Args:
        date_string: English date string to convert.

    Returns:
        Date string in ISO format (YYYY-MM-DD).

    Raises:
        AttributeError: If the date string format is not recognized.
        KeyError: If the month name is not recognized.
        ValueError: If the parsed date is invalid (e.g., February 30).
    """
    date_string = date_string.strip()
    regex_long_date_en = re.compile(
        r"(?P<monthL>[a-zA-Z\.]{3,9})\s+(?P<day>\d{1,2})(?:st|nd|rd|th)?,\s*(?P<year>\d\d\d\d)")
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
    """Converts long-format German dates to ISO format (YYYY-MM-DD).

    Parses German date strings in formats like "3. Oktober 1990" or
    "15. März 2021" and converts them to ISO 8601 date format.

    Args:
        date_string: German date string to convert.

    Returns:
        Date string in ISO format (YYYY-MM-DD).

    Raises:
        AttributeError: If the date string format is not recognized.
        KeyError: If the month name is not recognized.
        ValueError: If the parsed date is invalid (e.g., 30. Februar).
    """
    date_string = date_string.strip()
    regex_long_date_de = re.compile(
        r"(?P<day>\d{1,2})\.\s+(?P<monthL>[a-zA-ZÄä\.]{3,9})\s+(?P<year>\d{4})")
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
