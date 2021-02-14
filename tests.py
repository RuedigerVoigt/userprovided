#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Automatic Tests for userprovided

To run these tests with coverage:
coverage run --source userprovided -m pytest tests.py
To generate a report afterwards.
coverage html
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
(c) 2020-2021 Rüdiger Voigt
Released under the Apache License 2.0
"""

import pathlib

from hypothesis import given
from hypothesis import settings
from hypothesis import Verbosity
from hypothesis.strategies import emails
from hypothesis.strategies import dates
import pytest


import userprovided


def test_hash_available():
    with pytest.raises(ValueError):
        userprovided.hash.hash_available('md5', True)
    with pytest.raises(ValueError):
        userprovided.hash.hash_available('sha1', True)
    with pytest.raises(ValueError):
        userprovided.hash.hash_available(None, True)
    with pytest.raises(ValueError):
        userprovided.hash.hash_available('  ', True)
    assert userprovided.hash.hash_available('sha224', True) is True
    assert userprovided.hash.hash_available('sha256', True) is True
    assert userprovided.hash.hash_available('sha512', True) is True
    assert userprovided.hash.hash_available('NonExistentHash', True) is False


def test_calculate_file_hash():
    # Path is non-existent:
    with pytest.raises(FileNotFoundError):
        userprovided.hash.calculate_file_hash('some/random/string/qwertzuiopü',
                                              'sha256')
    # Deprecated hash methods:
    with pytest.raises(NotImplementedError):
        userprovided.hash.calculate_file_hash(pathlib.Path('.'), 'md5')
    with pytest.raises(NotImplementedError):
        userprovided.hash.calculate_file_hash(pathlib.Path('.'), 'sha1')
    # Non Existent hash method:
    with pytest.raises(ValueError):
        userprovided.hash.calculate_file_hash(pathlib.Path('.'),
                                              'non-existent-hash')
    # Not supported hash method (available, but not an option):
    with pytest.raises(ValueError):
        userprovided.hash.calculate_file_hash(pathlib.Path('.'), 'sha384')
    # Default is fallback to SHA256
    assert userprovided.hash.calculate_file_hash(pathlib.Path('testfile')) == '2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae'
    # SHA224
    assert userprovided.hash.calculate_file_hash(pathlib.Path('testfile'), 'sha224') == '0808f64e60d58979fcb676c96ec938270dea42445aeefcd3a4e6f8db'
    # SHA512
    assert userprovided.hash.calculate_file_hash(pathlib.Path('testfile'), 'sha512') == 'f7fbba6e0636f890e56fbbf3283e524c6fa3204ae298382d624741d0dc6638326e282c41be5e4254d8820772c5518a2c5a8c0c7f7eda19594a7eb539453e1ed7'


def test_mail_is_email():
    assert userprovided.mail.is_email('test@example.com') is True
    assert userprovided.mail.is_email('test@example-example.com') is True
    assert userprovided.mail.is_email('test@example.co.uk') is True
    assert userprovided.mail.is_email('  test@example.com  ') is True
    assert userprovided.mail.is_email('test+filter@example.com') is True
    assert userprovided.mail.is_email('@example.com') is False
    assert userprovided.mail.is_email('test@@example.com') is False
    assert userprovided.mail.is_email('test@example.') is False
    assert userprovided.mail.is_email(None) is False
    assert userprovided.mail.is_email('') is False
    assert userprovided.mail.is_email('   ') is False


@settings(max_examples=1000,
          print_blob=True,
          verbosity=Verbosity.normal)
@given(x=emails())
def test_hypothesis_mail_is_email(x):
    assert userprovided.mail.is_email(x) is True


def test_cloud_is_aws_s3_bucket_name():
    assert userprovided.cloud.is_aws_s3_bucket_name('abc') is True
    # perfectly fine at max length:
    assert userprovided.cloud.is_aws_s3_bucket_name(
            'iekoht9choofe9eixeeseizoo0iuzos1ibeepae7phee3aeghai7shal9kiepiy') is True
    # too short:
    assert userprovided.cloud.is_aws_s3_bucket_name('ab') is False
    # too long:
    assert userprovided.cloud.is_aws_s3_bucket_name(
        'iekoht9choofe9eixeeseizoo0iuzos1ibeepae7phee3aeghaif7shal9kiepiy') is False
    # IPv4:
    assert userprovided.cloud.is_aws_s3_bucket_name('127.0.0.1') is False
    # invalid characters:
    assert userprovided.cloud.is_aws_s3_bucket_name('iekoht9choofe9ei_xeeseizo') is False
    assert userprovided.cloud.is_aws_s3_bucket_name('iekoh#xeeseizo') is False
    assert userprovided.cloud.is_aws_s3_bucket_name('ab$$c') is False
    assert userprovided.cloud.is_aws_s3_bucket_name('ABc') is False
    # starting with lowercase letter or number ?????????????????????????????????????????????????????
    assert userprovided.cloud.is_aws_s3_bucket_name('-abc') is False
    # containing dots:
    assert userprovided.cloud.is_aws_s3_bucket_name('iekoht9choofe.eixeeseizoo0iuzos1ibee.pae7ph') is True


def test_is_url():
    # missing scheme:
    assert userprovided.url.is_url('noscheme.example.com') is False
    # wrong scheme:
    assert userprovided.url.is_url('ftp://example.com', ('http', 'https')) is False
    # scheme with typo (one instead of two slashes):
    assert userprovided.url.is_url('https:/example.com') is False
    # valid URLs:
    assert userprovided.url.is_url('https://example.com') is True
    assert userprovided.url.is_url('https://example.com', ('https', 'http')) is True
    assert userprovided.url.is_url('https://example.com', ('https')) is True
    assert userprovided.url.is_url('https://subdomain.example.com') is True
    assert userprovided.url.is_url('https://example.com/index.php?id=42') is True


def test_normalize_query_part():
    # By mistake a full URL is provided instead of only the query part:
    with pytest.raises(ValueError):
        userprovided.url.normalize_query_part('https://www.example.com/index.php?foo=foo&foo=bar')
    # Duplicate key in query part of URL query with conflicting values:
    with pytest.raises(ValueError):
        userprovided.url.normalize_query_part('foo=foo&foo=bar')
    # Duplicate key in query part of URL with the same value:
    assert userprovided.url.normalize_query_part('foo=bar&foo=bar') == 'foo=bar'
    # Chunk of query is malformed: the = is missing:
    assert userprovided.url.normalize_query_part('missingequalsign&foo=bar') == 'foo=bar'
    assert userprovided.url.normalize_query_part('foo=bar&missingequalsign&') == 'foo=bar'


def test_normalize_url():
    # remove whitespace around the URL:
    assert userprovided.url.normalize_url(' https://www.example.com/ ') == 'https://www.example.com/'
    # Convert scheme and hostname to lowercase
    assert userprovided.url.normalize_url('HTTPS://www.ExAmPlE.com') == 'https://www.example.com'
    # Remove standard port for scheme (http)
    assert userprovided.url.normalize_url('http://www.example.com:80') == 'http://www.example.com'
    # Remove standard port for scheme (https)
    assert userprovided.url.normalize_url('https://www.example.com:443') == 'https://www.example.com'
    # Keep non-standard port for scheme (http)
    assert userprovided.url.normalize_url('https://www.example.com:123') =='https://www.example.com:123'
    # Remove duplicate slashes from the path (1)
    assert userprovided.url.normalize_url('https://www.example.com//index.html') == 'https://www.example.com/index.html'
    # Remove duplicate slashes from the path (2)
    assert userprovided.url.normalize_url('https://www.example.com/en//index.html') == 'https://www.example.com/en/index.html'
    # remove fragment when query is not present
    assert userprovided.url.normalize_url(' https://www.example.com/index.html#test ') == 'https://www.example.com/index.html'
    # remove fragment when query is present
    assert userprovided.url.normalize_url(' https://www.example.com/index.php?name=foo#test ') == 'https://www.example.com/index.php?name=foo'
    # remove fragment when path is not present
    assert userprovided.url.normalize_url(' https://www.example.com/#test ') == 'https://www.example.com/'
    # Ignore empty query
    assert userprovided.url.normalize_url('https://www.example.com/index.php?') == 'https://www.example.com/index.php'
    # remove empty elements of the query part
    assert userprovided.url.normalize_url('https://www.example.com/index.php?name=foo&example=') == 'https://www.example.com/index.php?name=foo'
    # order the elements in the query part by alphabet
    assert userprovided.url.normalize_url('https://www.example.com/index.py?c=3&a=1&b=2') == 'https://www.example.com/index.py?a=1&b=2&c=3'
    # URL with non standard query part (does not follow key=value syntax).
    # Mentioned in RFC 3986 as "erroneous" because it mixes query and path.
    # However still used by some software.
    assert userprovided.url.normalize_url('https://www.example.com/forums/forumdisplay.php?example-forum') == 'https://www.example.com/forums/forumdisplay.php?example-forum'
    # Empty query, but '?' indicating one
    assert userprovided.url.normalize_url('https://www.example.com/index.php?') == 'https://www.example.com/index.php'
    # input is not an URL
    with pytest.raises(ValueError):
        userprovided.url.normalize_url('somestring')


def test_determine_file_extension():
    # URL hint matches server header
    assert userprovided.url.determine_file_extension('https://www.example.com/example.pdf', 'application/pdf') == '.pdf'
    # URL does not provide a hint, but the HTTP header does
    assert userprovided.url.determine_file_extension('https://www.example.com/', 'text/html') == '.html'
    # URL hint and HTTP header contradict each other!
    # Fallback to suffix suggested by URL:
    assert userprovided.url.determine_file_extension('https://www.example.com/example.pdf', 'text/html') == '.pdf'
    # no server header, but hint in URL
    assert userprovided.url.determine_file_extension('https://www.example.com/example.pdf', '') == '.pdf'
    # no hint at all
    assert userprovided.url.determine_file_extension('https://www.example.com/', '') == '.unknown'
    # malformed server header and no hint in the URL
    assert userprovided.url.determine_file_extension('https://www.example.com/', 'malformed/nonexist') == '.unknown'
    # unknown extension in URL and no mime-type by server
    assert userprovided.url.determine_file_extension('https://www.example.com/index.foo', None) == '.unknown'
    # text/plain
    assert userprovided.url.determine_file_extension('https://www.example.com/test.txt', 'text/plain') == '.txt'
    # .htm -> html
    assert userprovided.url.determine_file_extension('https://www.example.com/test.htm', 'text/plain') == '.html'
    assert userprovided.url.determine_file_extension('https://www.example.com/test.htm', 'doesnotmatter') == '.html'


def test_date_exists_non_numeric():
    assert userprovided.date.date_exists('2021', '01', 'a') is False
    assert userprovided.date.date_exists('2021', 'a', '01') is False
    assert userprovided.date.date_exists('a', '01', '01') is False


@settings(print_blob=True,
          verbosity=Verbosity.normal)
@given(x=dates())
def test_date_exists(x):
    assert userprovided.date.date_exists(x.year, x.month, x.day) is True


def test_date_en_long_to_iso():
    # valid input:
    assert userprovided.date.date_en_long_to_iso('Jul. 4, 1776') == '1776-07-04'
    assert userprovided.date.date_en_long_to_iso('May 8, 1945') == '1945-05-08'
    assert userprovided.date.date_en_long_to_iso('May 08, 1945') == '1945-05-08'
    assert userprovided.date.date_en_long_to_iso('October 3, 1990') == '1990-10-03'
    assert userprovided.date.date_en_long_to_iso('November 03, 2020') == '2020-11-03'
    # messed up whitespace:
    assert userprovided.date.date_en_long_to_iso('Jul. 4,      1776') == '1776-07-04'
    assert userprovided.date.date_en_long_to_iso('Jul. 4,1776') == '1776-07-04'
    assert userprovided.date.date_en_long_to_iso('   Jul. 4, 1776  ') == '1776-07-04'
    assert userprovided.date.date_en_long_to_iso('Jul.    4, 1776') == '1776-07-04'
    # grammatically incorrect, but clear:
    assert userprovided.date.date_en_long_to_iso('May 8th, 1945') == '1945-05-08'
    # upper and lower case:
    assert userprovided.date.date_en_long_to_iso('jul. 4, 1776') == '1776-07-04'
    assert userprovided.date.date_en_long_to_iso('JUL. 4, 1776') == '1776-07-04'
    # leap year:
    assert userprovided.date.date_en_long_to_iso('February 29, 2020') == '2020-02-29'
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


def test_port_in_range():
    assert userprovided.port.port_in_range(443) is True
    assert userprovided.port.port_in_range(65537) is False
    assert userprovided.port.port_in_range(-1) is False
    with pytest.raises(ValueError):
        userprovided.port.port_in_range('foo')
    with pytest.raises(ValueError):
        userprovided.port.port_in_range(None)


def test_convert_to_set():
    # single string with multiple characters
    # (wrong would be making each character into an element)
    assert userprovided.parameters.convert_to_set('abc') == {'abc'}
    # list with duplicates to set
    assert userprovided.parameters.convert_to_set(['a', 'a', 'b', 'c']) == {'a', 'b', 'c'}
    # tuple with duplicates
    assert userprovided.parameters.convert_to_set(('a', 'a', 'b', 'c')) == {'a', 'b', 'c'}
    # set should return unchanged
    assert userprovided.parameters.convert_to_set({'a', 'b', 'c'}) == {'a', 'b', 'c'}
    # unsupported data type integer
    with pytest.raises(TypeError):
        userprovided.parameters.convert_to_set(3)


def test_validate_dict_keys():
    # not a dictionary
    with pytest.raises(AttributeError):
        userprovided.parameters.validate_dict_keys(
            {'a', 'b', 'c'},
            {'a', 'b'})
    # unknown key in dictionary, but no necessary keys
    with pytest.raises(ValueError):
        userprovided.parameters.validate_dict_keys(
            {'a': 1, 'b': 2, 'c': 3},
            {'a', 'b'})
    # missing a necessary key in dictionary to test
    with pytest.raises(ValueError):
        userprovided.parameters.validate_dict_keys(
            {'a': 1, 'b': 2},
            {'a', 'b', 'c'},
            {'b', 'c'})
    # necessary_keys contains a key missing in allowed_keys
    with pytest.raises(ValueError):
        userprovided.parameters.validate_dict_keys(
            {'a': 1, 'b': 2, 'c': 3},
            {'a', 'b', 'c'},
            {'b', 'c', 'd'})
    # Valid:
    assert userprovided.parameters.validate_dict_keys(
            {'a': 1, 'b': 2},
            {'a', 'b', 'c'},
            {'a', 'b'},
            'name') is True


def test_numeric_in_range():
    # Minimum value larger than maximum value
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range(
            'example',
            101,
            100,
            1.0,
            50)

    # Fallback value outside the allowed range
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range(
            'example',
            101,
            100,
            200,
            5000  # fallback larger than maximum
            )
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range(
            'example',
            101,
            100,
            200,
            0  # fallback smaller than minimum
            )

    # One of the values not numeric
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range(
            'example',
            'some string',
            100,
            1.0,
            0)
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range(
            'example',
            101,
            'some string',
            1.0,
            0)
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range(
            'example',
            101,
            100,
            'some string',
            0)
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range(
            'example',
            101,
            100,
            1.0,
            'some string')
    # no paramter name
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range(
            None,
            101,
            100,
            1.0,
            'some string')

    # given value within range
    assert userprovided.parameters.numeric_in_range('example', 10.0, 1, 100, 50) == 10.0

    # given value too large => fallback
    assert userprovided.parameters.numeric_in_range('example', 101, 1, 100, 50) == 50

    # given value to small => fallback
    assert userprovided.parameters.numeric_in_range('example', 3, 10, 100, 50) == 50


def test_int_in_range():
    # parmeter is not integer
    with pytest.raises(ValueError):
        userprovided.parameters.int_in_range(
            'example',
            10,
            1,
            100.0,
            50)
    # parameter is string
    with pytest.raises(ValueError):
        userprovided.parameters.int_in_range(
            'example',
            10,
            1,
            'foo',
            50)
    # given value within range
    assert userprovided.parameters.int_in_range('foo', 10, 1, 100, 50) == 10
    # given value to small => fallback
    assert userprovided.parameters.int_in_range('foo', 3, 10, 100, 50) == 50


def test_string_in_range():
    # string within range
    assert userprovided.parameters.string_in_range('foo', 1, 5) is True
    # default is to apply strip() to the string
    assert userprovided.parameters.string_in_range('     foo      ', 3, 3) is True
    # switch off strip()
    assert userprovided.parameters.string_in_range('     foo      ', 3, 3, False) is False
    # string too long
    assert userprovided.parameters.string_in_range('     foo      ', 1, 2) is False
    # string to short
    assert userprovided.parameters.string_in_range('     foo      ', 5, 10) is False
    # parameters contradict each other
    with pytest.raises(ValueError):
        userprovided.parameters.string_in_range('example', 10, 5)


def test_enforce_boolean():
    # string instead of boolean
    with pytest.raises(ValueError):
        userprovided.parameters.enforce_boolean('True')
    # numeric instead of boolean
    with pytest.raises(ValueError):
        userprovided.parameters.enforce_boolean(1)
    # set parameter_name
    with pytest.raises(ValueError):
        userprovided.parameters.enforce_boolean(1, 'example')
    # valid calls:
    userprovided.parameters.enforce_boolean(True)
    userprovided.parameters.enforce_boolean(False)
