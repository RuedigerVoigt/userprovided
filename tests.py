#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hypothesis import given
from hypothesis import settings
from hypothesis import Verbosity
from hypothesis.strategies import emails
from hypothesis.strategies import dates
import unittest
from unittest.mock import patch, mock_open
import pathlib

import userprovided


class BotTest(unittest.TestCase):

    def test_hash_available(self):
        self.assertRaises(ValueError,
                          userprovided.hash.hash_available, 'md5', True)
        self.assertRaises(ValueError,
                          userprovided.hash.hash_available, 'sha1', True)
        self.assertRaises(ValueError,
                          userprovided.hash.hash_available, None, True)
        self.assertRaises(ValueError,
                          userprovided.hash.hash_available, '  ', True)
        self.assertTrue(userprovided.hash.hash_available('sha224'))
        self.assertTrue(userprovided.hash.hash_available('sha256'))
        self.assertTrue(userprovided.hash.hash_available('sha512'))
        self.assertFalse(userprovided.hash.hash_available('NonExistentHash'))

    def test_calculate_file_hash(self):
        # Path is non-existent:
        self.assertRaises(FileNotFoundError,
                          userprovided.hash.calculate_file_hash,
                          'some/random/string/qwertzuiopü', 'sha256')
        # Deprecated hash methods:
        self.assertRaises(NotImplementedError,
                          userprovided.hash.calculate_file_hash,
                          pathlib.Path('.'), 'md5')
        self.assertRaises(NotImplementedError,
                          userprovided.hash.calculate_file_hash,
                          pathlib.Path('.'), 'sha1')
        # Non Existent hash method:
        self.assertRaises(ValueError,
                          userprovided.hash.calculate_file_hash,
                          pathlib.Path('.'), 'non-existent-hash')
        # Not supported hash method (available, but not an option):
        self.assertRaises(ValueError,
                          userprovided.hash.calculate_file_hash,
                          pathlib.Path('.'), 'sha384')

        # Default is fallback to SHA256
        self.assertEqual(
            userprovided.hash.calculate_file_hash(pathlib.Path('testfile')),
                '2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae'
        )
        # SHA224
        self.assertEqual(
            userprovided.hash.calculate_file_hash(pathlib.Path('testfile'), 'sha224'),
                '0808f64e60d58979fcb676c96ec938270dea42445aeefcd3a4e6f8db'
        )
        # SHA512
        self.assertEqual(
            userprovided.hash.calculate_file_hash(pathlib.Path('testfile'), 'sha512'),
                'f7fbba6e0636f890e56fbbf3283e524c6fa3204ae298382d624741d0dc6638326e282c41be5e4254d8820772c5518a2c5a8c0c7f7eda19594a7eb539453e1ed7'
        )

    def test_mail_is_email(self):
        self.assertTrue(userprovided.mail.is_email('test@example.com'))
        self.assertTrue(userprovided.mail.is_email('test@example-example.com'))
        self.assertTrue(userprovided.mail.is_email('test@example.co.uk'))
        self.assertTrue(userprovided.mail.is_email('  test@example.com  '))
        self.assertTrue(userprovided.mail.is_email('test+filter@example.com'))
        self.assertFalse(userprovided.mail.is_email('@example.com'))
        self.assertFalse(userprovided.mail.is_email('test@@example.com'))
        self.assertFalse(userprovided.mail.is_email('test@example.'))
        self.assertFalse(userprovided.mail.is_email(None))
        self.assertFalse(userprovided.mail.is_email(''))
        self.assertFalse(userprovided.mail.is_email('   '))

    @settings(max_examples=1000,
              print_blob=True,
              verbosity=Verbosity.normal)
    @given(x=emails())
    def test_hypothesis_mail_is_email(self, x):
        self.assertTrue(userprovided.mail.is_email(x))

    def test_cloud_is_aws_s3_bucket_name(self):
        self.assertTrue(userprovided.cloud.is_aws_s3_bucket_name('abc'))
        # too short
        self.assertFalse(userprovided.cloud.is_aws_s3_bucket_name('ab'))
        # too long
        self.assertFalse(userprovided.cloud.is_aws_s3_bucket_name(
            'iekoht9choofe9eixeeseizoo0iuzos1ibeepae7phee3aeghaif7shal9kiepiy')
            )
        # Ipv4 address
        self.assertFalse(userprovided.cloud.is_aws_s3_bucket_name('127.0.0.1'))
        # invalid characters
        self.assertFalse(userprovided.cloud.is_aws_s3_bucket_name(
            'iekoht9choofe9ei_xeeseizo'))
        self.assertFalse(userprovided.cloud.is_aws_s3_bucket_name(
            'iekoh#xeeseizo'))
        self.assertFalse(userprovided.cloud.is_aws_s3_bucket_name('ab$$c'))
        self.assertFalse(userprovided.cloud.is_aws_s3_bucket_name('ABc'))
        # starting with lowercase letter or number
        self.assertFalse(userprovided.cloud.is_aws_s3_bucket_name('-abc'))
        # prefectly fine at max length
        self.assertTrue(userprovided.cloud.is_aws_s3_bucket_name(
            'iekoht9choofe9eixeeseizoo0iuzos1ibeepae7phee3aeghai7shal9kiepiy'))
        # containing dots
        self.assertTrue(userprovided.cloud.is_aws_s3_bucket_name(
            'iekoht9choofe.eixeeseizoo0iuzos1ibee.pae7ph'))

    def test_is_url(self):
        # missing scheme
        self.assertFalse(userprovided.url.is_url('noscheme.example.com'))
        # wrong scheme
        self.assertFalse(userprovided.url.is_url(
            'ftp://example.com',
            ('http', 'https')))
        # scheme with typo (one instead of two slashes)
        self.assertFalse(userprovided.url.is_url('https:/example.com'))
        # valid URLs
        self.assertTrue(
            userprovided.url.is_url('https://example.com'))
        self.assertTrue(
            userprovided.url.is_url(
                'https://example.com',
                ('https', 'http')))
        self.assertTrue(
            userprovided.url.is_url(
                'https://example.com',
                ('https')))
        self.assertTrue(
            userprovided.url.is_url('https://subdomain.example.com'))
        self.assertTrue(
            userprovided.url.is_url('https://example.com/index.php?id=42'))

    def test_normalize_query_part(self):
        # By mistake a full URL is provided instead of only the query part
        self.assertRaises(ValueError,
                          userprovided.url.normalize_query_part,
                          'https://www.example.com/index.php?foo=foo&foo=bar')
        # Duplicate key in query part of URL query with conflicting values
        self.assertRaises(ValueError,
                          userprovided.url.normalize_query_part,
                          'foo=foo&foo=bar')
        # Duplicate key in query part of URL with the same value
        self.assertEqual(userprovided.url.normalize_query_part(
                         'foo=bar&foo=bar'), 'foo=bar')
        # Chunk of query is malformed: the = is missing
        self.assertEqual(userprovided.url.normalize_query_part(
                         'missingequalsign&foo=bar'), 'foo=bar')
        self.assertEqual(userprovided.url.normalize_query_part(
                         'foo=bar&missingequalsign&'), 'foo=bar')

    def test_normalize_url(self):
        # remove whitespace around the URL
        self.assertEqual(userprovided.url.normalize_url(
            ' https://www.example.com/ '),
            'https://www.example.com/')
        # Convert scheme and hostname to lowercase
        self.assertEqual(userprovided.url.normalize_url(
            'HTTPS://www.ExAmPlE.com'),
            'https://www.example.com')
        # Remove standard port for scheme (http)
        self.assertEqual(userprovided.url.normalize_url(
            'http://www.example.com:80'),
            'http://www.example.com')
        # Remove standard port for scheme (https)
        self.assertEqual(userprovided.url.normalize_url(
            'https://www.example.com:443'),
            'https://www.example.com')
        # Keep non-standard port for scheme (http)
        self.assertEqual(userprovided.url.normalize_url(
            'https://www.example.com:123'),
            'https://www.example.com:123')
        # Remove duplicate slashes from the path (1)
        self.assertEqual(userprovided.url.normalize_url(
            'https://www.example.com//index.html'),
            'https://www.example.com/index.html')
        # Remove duplicate slashes from the path (2)
        self.assertEqual(userprovided.url.normalize_url(
            'https://www.example.com/en//index.html'),
            'https://www.example.com/en/index.html')
        # remove fragment when query is not present
        self.assertEqual(userprovided.url.normalize_url(
            ' https://www.example.com/index.html#test '),
            'https://www.example.com/index.html')
        # remove fragment when query is present
        self.assertEqual(userprovided.url.normalize_url(
            ' https://www.example.com/index.php?name=foo#test '),
            'https://www.example.com/index.php?name=foo')
        # remove fragment when path is not present
        self.assertEqual(userprovided.url.normalize_url(
            ' https://www.example.com/#test '),
            'https://www.example.com/')
        # Ignore empty query
        self.assertEqual(userprovided.url.normalize_url(
            'https://www.example.com/index.php?'),
            'https://www.example.com/index.php')
        # remove empty elements of the query part
        self.assertEqual(userprovided.url.normalize_url(
            'https://www.example.com/index.php?name=foo&example='),
            'https://www.example.com/index.php?name=foo')
        # order the elements in the query part by alphabet
        self.assertEqual(userprovided.url.normalize_url(
            'https://www.example.com/index.py?c=3&a=1&b=2'),
            'https://www.example.com/index.py?a=1&b=2&c=3')
        # URL with non standard query part (does not follow key=value syntax).
        # Mentioned in RFC 3986 as "erroneous" because it mixes query and path.
        # However still used by some software.
        self.assertEqual(userprovided.url.normalize_url(
            'https://www.example.com/forums/forumdisplay.php?example-forum'),
            'https://www.example.com/forums/forumdisplay.php?example-forum')
        # Empty query, but '?' indicating one
        self.assertEqual(userprovided.url.normalize_url(
            'https://www.example.com/index.php?'),
            'https://www.example.com/index.php')
        # input is not an URL
        self.assertRaises(ValueError,
                          userprovided.url.normalize_url,
                          'somestring')

    def test_determine_file_extension(self):
        # URL hint matches server header
        self.assertEqual(userprovided.url.determine_file_extension(
            'https://www.example.com/example.pdf',
            'application/pdf'), '.pdf')
        # URL does not provide a hint, but the HTTP header does
        self.assertEqual(userprovided.url.determine_file_extension(
            'https://www.example.com/',
            'text/html'), '.html')
        # URL hint and HTTP header contradict each other
        # Fallback to suggested by URL
        self.assertEqual(userprovided.url.determine_file_extension(
            'https://www.example.com/example.pdf',
            'text/html'), '.pdf')
        # no server header, but hint in URL
        self.assertEqual(userprovided.url.determine_file_extension(
            'https://www.example.com/example.pdf', ''), '.pdf')
        # no hint at all
        self.assertEqual(userprovided.url.determine_file_extension(
            'https://www.example.com/', ''), '.unknown')
        # malformed server header and no hint in the URL
        self.assertEqual(userprovided.url.determine_file_extension(
            'https://www.example.com/', 'malformed/nonexist'), '.unknown')
        # unknown extension in URL and no mime-type by server
        self.assertEqual(userprovided.url.determine_file_extension(
            'https://www.example.com/index.foo', None), '.unknown')  
        # text/plain
        self.assertEqual(userprovided.url.determine_file_extension(
            'https://www.example.com/test.txt', 'text/plain'), '.txt')
        # .htm -> html
        self.assertEqual(userprovided.url.determine_file_extension(
            'https://www.example.com/test.htm', 'text/plain'), '.html')
        self.assertEqual(userprovided.url.determine_file_extension(
            'https://www.example.com/test.htm', 'doesnotmatter'), '.html')

    @settings(print_blob=True,
              verbosity=Verbosity.normal)
    @given(x=dates())
    def test_date_exists(self, x):
        self.assertTrue(userprovided.date.date_exists(x.year, x.month, x.day))

    def test_date_exists_non_numeric(self):
        self.assertFalse(userprovided.date.date_exists('2021', '01', 'a'))
        self.assertFalse(userprovided.date.date_exists('2021', 'a', '01'))
        self.assertFalse(userprovided.date.date_exists('a', '01', '01'))

    def test_date_en_long_to_iso(self):
        # valid input:
        self.assertEqual(
            userprovided.date.date_en_long_to_iso('Jul. 4, 1776'),
            '1776-07-04')
        self.assertEqual(
            userprovided.date.date_en_long_to_iso('May 8, 1945'),
            '1945-05-08')
        self.assertEqual(
            userprovided.date.date_en_long_to_iso('May 08, 1945'),
            '1945-05-08')
        self.assertEqual(
            userprovided.date.date_en_long_to_iso('October 3, 1990'),
            '1990-10-03')
        self.assertEqual(
            userprovided.date.date_en_long_to_iso('November 03, 2020'),
            '2020-11-03')
        # messed up whitespace:
        self.assertEqual(
            userprovided.date.date_en_long_to_iso('Jul. 4,      1776'),
            '1776-07-04')
        self.assertEqual(
            userprovided.date.date_en_long_to_iso('Jul. 4,1776'),
            '1776-07-04')
        self.assertEqual(
            userprovided.date.date_en_long_to_iso('   Jul. 4, 1776  '),
            '1776-07-04')
        self.assertEqual(
            userprovided.date.date_en_long_to_iso('Jul.    4, 1776'),
            '1776-07-04')
        # grammatically incorrect, but clear:
        self.assertEqual(
            userprovided.date.date_en_long_to_iso('May 8th, 1945'),
            '1945-05-08')
        # upper and lower case:
        self.assertEqual(
            userprovided.date.date_en_long_to_iso('jul. 4, 1776'),
            '1776-07-04')
        self.assertEqual(
            userprovided.date.date_en_long_to_iso('JUL. 4, 1776'),
            '1776-07-04')
        # leap year:
        self.assertEqual(
            userprovided.date.date_en_long_to_iso('February 29, 2020'),
            '2020-02-29')
        # non-existing date:
        self.assertRaises(ValueError,
                          userprovided.date.date_en_long_to_iso,
                          'February 30, 2020')
        # misspelled month:
        self.assertRaises(KeyError,
                          userprovided.date.date_en_long_to_iso,
                          'abcd 30, 2020')
        # incomplete dates (missing elements)
        self.assertRaises(AttributeError,
                          userprovided.date.date_en_long_to_iso,
                          'February, 2020')
        self.assertRaises(AttributeError,
                          userprovided.date.date_en_long_to_iso,
                          '30, 2020')
        self.assertRaises(AttributeError,
                          userprovided.date.date_en_long_to_iso,
                          'February 30')

    def test_port_in_range(self):
        self.assertTrue(userprovided.port.port_in_range(443))
        self.assertFalse(userprovided.port.port_in_range(65537))
        self.assertFalse(userprovided.port.port_in_range(-1))
        self.assertRaises(ValueError, userprovided.port.port_in_range, 'foo')
        self.assertRaises(ValueError, userprovided.port.port_in_range, None)

    def test_convert_to_set(self):
        # single string with multiple characters
        # (wrong would be making each character into an element)
        self.assertEqual(userprovided.parameters.convert_to_set('abc'),
                         {'abc'})
        # list with duplicates to set
        self.assertEqual(userprovided.parameters.convert_to_set(
                         ['a', 'a', 'b', 'c']),
                         {'a', 'b', 'c'})
        # tuple with duplicates
        self.assertEqual(userprovided.parameters.convert_to_set(
                         ('a', 'a', 'b', 'c')),
                         {'a', 'b', 'c'})
        # set should return unchanged
        self.assertEqual(userprovided.parameters.convert_to_set(
                         {'a', 'b', 'c'}),
                         {'a', 'b', 'c'})
        # unsupported data type integer
        self.assertRaises(TypeError, userprovided.parameters.convert_to_set, 3)

    def test_validate_dict_keys(self):
        # not a dictionary
        self.assertRaises(AttributeError,
                          userprovided.parameters.validate_dict_keys,
                          {'a', 'b', 'c'},
                          {'a', 'b'})
        # unknown key in dictionary, but no necessary keys
        self.assertRaises(ValueError,
                          userprovided.parameters.validate_dict_keys,
                          {'a': 1, 'b': 2, 'c': 3},
                          {'a', 'b'})
        # missing a necessary key in dictionary to test
        self.assertRaises(ValueError,
                          userprovided.parameters.validate_dict_keys,
                          {'a': 1, 'b': 2},
                          {'a', 'b', 'c'},
                          {'b', 'c'})
        # necessary_keys contains a key missing in allowed_keys
        self.assertRaises(ValueError,
                          userprovided.parameters.validate_dict_keys,
                          {'a': 1, 'b': 2, 'c': 3},
                          {'a', 'b', 'c'},
                          {'b', 'c', 'd'})
        self.assertTrue(userprovided.parameters.validate_dict_keys(
            {'a': 1, 'b': 2},
            {'a', 'b', 'c'},
            {'a', 'b'},
            'name'))

    def test_numeric_in_range(self):
        # Minimum value larger than maximum value
        self.assertRaises(ValueError,
                          userprovided.parameters.numeric_in_range,
                          'example',
                          101,
                          100,
                          1.0,
                          50)

        # Fallback value outside the allowed range
        self.assertRaises(ValueError,
                          userprovided.parameters.numeric_in_range,
                          'example',
                          101,
                          100,
                          200,
                          5000  # fallback larger than maximum
                          )
        self.assertRaises(ValueError,
                          userprovided.parameters.numeric_in_range,
                          'example',
                          101,
                          100,
                          200,
                          0  # fallback smaller than minimum
                          )

        # One of the values not numeric
        self.assertRaises(ValueError,
                          userprovided.parameters.numeric_in_range,
                          'example',
                          'some string',
                          100,
                          1.0,
                          0)
        self.assertRaises(ValueError,
                          userprovided.parameters.numeric_in_range,
                          'example',
                          101,
                          'some string',
                          1.0,
                          0)
        self.assertRaises(ValueError,
                          userprovided.parameters.numeric_in_range,
                          'example',
                          101,
                          100,
                          'some string',
                          0)
        self.assertRaises(ValueError,
                          userprovided.parameters.numeric_in_range,
                          'example',
                          101,
                          100,
                          1.0,
                          'some string')
        # no paramter name
        self.assertRaises(ValueError,
                          userprovided.parameters.numeric_in_range,
                          None,
                          101,
                          100,
                          1.0,
                          'some string')

        # given value within range
        self.assertEqual(
            userprovided.parameters.numeric_in_range(
                'example', 10.0, 1, 100, 50
            ),
            10.0
            )

        # given value too large => fallback
        self.assertEqual(
            userprovided.parameters.numeric_in_range(
                'example', 101, 1, 100, 50
            ),
            50
            )

        # given value to small => fallback
        self.assertEqual(
            userprovided.parameters.numeric_in_range(
                'example', 3, 10, 100, 50
            ),
            50
            )

    def test_int_in_range(self):
        # parmeter is not integer
        self.assertRaises(ValueError,
                          userprovided.parameters.int_in_range,
                          'example',
                          10,
                          1,
                          100.0,
                          50)
        # parameter is string
        self.assertRaises(ValueError,
                          userprovided.parameters.int_in_range,
                          'example',
                          10,
                          1,
                          'foo',
                          50)
        # given value within range
        self.assertEqual(
            userprovided.parameters.int_in_range(
                'example', 10, 1, 100, 50
            ),
            10
            )
        # given value to small => fallback
        self.assertEqual(
            userprovided.parameters.int_in_range(
                'example', 3, 10, 100, 50
            ),
            50
            )

    def test_string_in_range(self):
        # string within range
        self.assertTrue(
            userprovided.parameters.string_in_range(
                'foo', 1, 5
                ))

        # default is to apply strip() to the string
        self.assertTrue(
            userprovided.parameters.string_in_range(
                '     foo      ', 3, 3
                ))

        # switch off strip()
        self.assertFalse(
            userprovided.parameters.string_in_range(
                '     foo      ', 3, 3, False
                ))

        # string too long
        self.assertFalse(
            userprovided.parameters.string_in_range(
                '     foo      ', 1, 2
                ))

        # string to short
        self.assertFalse(
            userprovided.parameters.string_in_range(
                '     foo      ', 5, 10
                ))

        # parameters contradict each other
        self.assertRaises(ValueError,
                          userprovided.parameters.string_in_range,
                          'example', 10, 5)

    def test_enforce_boolean(self):
        # string instead of boolean
        self.assertRaises(ValueError,
                          userprovided.parameters.enforce_boolean,
                          'True')
        # numeric instead of boolean
        self.assertRaises(ValueError,
                          userprovided.parameters.enforce_boolean,
                          1)
        # set parameter_name
        self.assertRaises(ValueError,
                          userprovided.parameters.enforce_boolean,
                          1, 'example')


if __name__ == "__main__":
    unittest.main()
