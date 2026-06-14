#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for the date module of userprovided.
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
Released under the Apache License 2.0
"""

# ruff: noqa

from hypothesis import given
from hypothesis import settings
from hypothesis import Verbosity
from hypothesis.strategies import dates
import pytest

import userprovided


def test_date_exists_non_numeric():
    assert userprovided.date.date_exists('2021', '01', 'a') is False
    assert userprovided.date.date_exists('2021', 'a', '01') is False
    assert userprovided.date.date_exists('a', '01', '01') is False


@settings(print_blob=True,
          verbosity=Verbosity.normal)
@given(x=dates())
def test_date_exists(x):
    assert userprovided.date.date_exists(x.year, x.month, x.day) is True


@pytest.mark.parametrize("date_string,expected", [
    # valid input:
    ('Jul. 4, 1776', '1776-07-04'),
    ('May 8, 1945', '1945-05-08'),
    ('May 08, 1945', '1945-05-08'),
    ('October 3, 1990', '1990-10-03'),
    ('November 03, 2020', '2020-11-03'),
    # messed up whitespace:
    ('Jul. 4,      1776', '1776-07-04'),
    ('Jul. 4,1776', '1776-07-04'),
    ('   Jul. 4, 1776  ', '1776-07-04'),
    ('Jul.    4, 1776', '1776-07-04'),
    # ordinal suffixes:
    ('January 1st, 2025', '2025-01-01'),
    ('January 2nd, 2025', '2025-01-02'),
    ('January 3rd, 2025', '2025-01-03'),
    ('May 8th, 1945', '1945-05-08'),
    # upper and lower case:
    ('jul. 4, 1776', '1776-07-04'),
    ('JUL. 4, 1776', '1776-07-04'),
    # leap year:
    ('February 29, 2020', '2020-02-29')
    ])
def test_date_en_long_to_iso(date_string, expected):
    assert userprovided.date.date_en_long_to_iso(date_string) == expected


def test_date_en_long_to_iso_exceptions():
    # non-existing date:
    with pytest.raises(ValueError):
        userprovided.date.date_en_long_to_iso('February 30, 2020')
    # misspelled month:
    with pytest.raises(KeyError):
        userprovided.date.date_en_long_to_iso('abcd 30, 2020')
    # incomplete dates (missing elements):
    with pytest.raises(AttributeError):
        userprovided.date.date_en_long_to_iso('February, 2020')
    with pytest.raises(AttributeError):
        userprovided.date.date_en_long_to_iso('30, 2020')
    with pytest.raises(AttributeError):
        userprovided.date.date_en_long_to_iso('February 30')


@pytest.mark.parametrize("date_string,expected", [
    # valid input:
    ('4. Jul. 1776', '1776-07-04'),
    ('8. Mai 1945', '1945-05-08'),
    ('15. März 2021', '2021-03-15'),
    ('15. MÄRZ 2021', '2021-03-15'),
    ('3. Oktober 1990', '1990-10-03'),
    ('03. November 2020', '2020-11-03'),
    # messed up whitespace:
    ('4. Jul.      1776', '1776-07-04'),
    ('4. Juli 1776', '1776-07-04'),
    ('   4. Juli 1776  ', '1776-07-04'),
    ('4.         Juli 1776', '1776-07-04'),
    # upper and lower case:
    ('4. julI 1776', '1776-07-04'),
    ('4. JUL. 1776', '1776-07-04'),
    # leap year:
    ('29. Februar 2020', '2020-02-29')
    ])
def test_date_de_long_to_iso(date_string, expected):
    assert userprovided.date.date_de_long_to_iso(date_string) == expected


def test_date_de_long_to_iso_exceptions():
    # non-existing date:
    with pytest.raises(ValueError):
        userprovided.date.date_de_long_to_iso('30. Februar 2020')
    # misspelled month:
    with pytest.raises(KeyError):
        userprovided.date.date_de_long_to_iso('30. abcd 2020')
    # incomplete dates (missing elements):
    with pytest.raises(AttributeError):
        userprovided.date.date_de_long_to_iso('Februar 2020')
    with pytest.raises(AttributeError):
        userprovided.date.date_de_long_to_iso('30 2020')
    with pytest.raises(AttributeError):
        userprovided.date.date_de_long_to_iso('Februar 30')
