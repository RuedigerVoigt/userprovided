#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hypothesis import given
from hypothesis import settings
from hypothesis import Verbosity
from hypothesis.strategies import emails
from hypothesis.strategies import dates
import unittest
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


if __name__ == "__main__":
    unittest.main()
