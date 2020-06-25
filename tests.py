#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hypothesis import given
from hypothesis import settings
from hypothesis import Verbosity
from hypothesis.strategies import emails
from hypothesis.strategies import dates
import unittest
import unittest.mock as mock
import pathlib

import userprovided


class BotTest(unittest.TestCase):

    def test_hash_available(self):
        self.assertRaises(ValueError,
                          userprovided.hash.hash_available, 'md5', True)
        self.assertRaises(ValueError,
                          userprovided.hash.hash_available, 'sha1', True)
        self.assertTrue(userprovided.hash.hash_available('sha224'))
        self.assertTrue(userprovided.hash.hash_available('sha256'))
        self.assertTrue(userprovided.hash.hash_available('sha512'))
        self.assertFalse(userprovided.hash.hash_available('NonExistentHash'))

    def test_calculate_file_hash(self):
        # Path is not a pathlib object:
        self.assertRaises(ValueError,
                          userprovided.hash.calculate_file_hash,
                          'some/random/string', 'sha256')
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

        # TO DO: mock file, for now works fine in manual test
#        self.assertEqual(
#            userprovided.hash.calculate_file_hash(
#                pathlib.Path('mocked-file.txt')),
#                '2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae'
#        )

    def test_mail_is_email(self):
        self.assertTrue(userprovided.mail.is_email('test@example.com'))
        self.assertTrue(userprovided.mail.is_email('test@example-example.com'))
        self.assertTrue(userprovided.mail.is_email('test@example.co.uk'))
        self.assertTrue(userprovided.mail.is_email('  test@example.com  '))
        self.assertTrue(userprovided.mail.is_email('test+filter@example.com'))
        self.assertFalse(userprovided.mail.is_email('@example.com'))
        self.assertFalse(userprovided.mail.is_email('test@@example.com'))
        self.assertFalse(userprovided.mail.is_email('test@example.'))

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

    @settings(print_blob=True,
              verbosity=Verbosity.normal)
    @given(x=dates())
    def test_date_exists(self, x):
        self.assertTrue(userprovided.date.date_exists(x.year, x.month, x.day))

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
        self.assertEqual(userprovided.parameters.convert_to_set('abc'), {'abc'})
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


if __name__ == "__main__":
    unittest.main()
