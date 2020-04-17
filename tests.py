#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hypothesis import given
from hypothesis import settings
from hypothesis import Verbosity
from hypothesis.strategies import emails
import unittest
import userprovided


class BotTest(unittest.TestCase):

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


if __name__ == "__main__":
    unittest.main()
