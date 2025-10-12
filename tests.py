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
(c) 2020-2025 Rüdiger Voigt
Released under the Apache License 2.0
"""

# flake8: noqa

from unittest.mock import patch
import pathlib

from hypothesis import given
from hypothesis import settings
from hypothesis import Verbosity
from hypothesis import HealthCheck
from hypothesis.strategies import emails
from hypothesis.strategies import dates
import pytest


import userprovided


def test_hash_available():
    # Deprecated algorithms
    with pytest.raises(userprovided.err.DeprecatedHashAlgorithm):
        userprovided.hashing.hash_available('md5', True)
    with pytest.raises(userprovided.err.DeprecatedHashAlgorithm):
        userprovided.hashing.hash_available('sha1', True)
    with pytest.raises(userprovided.err.DeprecatedHashAlgorithm):
        userprovided.hashing.hash_available('md5-sha1', True)
    # Invalid input
    with pytest.raises(ValueError):
        userprovided.hashing.hash_available(None, True)
    with pytest.raises(ValueError):
        userprovided.hashing.hash_available('  ', True)
    # SHA-2 family (guaranteed in Python 3.10+)
    assert userprovided.hashing.hash_available('sha224', True) is True
    assert userprovided.hashing.hash_available('sha256', True) is True
    assert userprovided.hashing.hash_available('sha384', True) is True
    assert userprovided.hashing.hash_available('sha512', True) is True
    # SHA-3 family (guaranteed in Python 3.10+)
    assert userprovided.hashing.hash_available('sha3_224', True) is True
    assert userprovided.hashing.hash_available('sha3_256', True) is True
    assert userprovided.hashing.hash_available('sha3_384', True) is True
    assert userprovided.hashing.hash_available('sha3_512', True) is True
    # BLAKE2 family (guaranteed in Python 3.10+)
    assert userprovided.hashing.hash_available('blake2b', True) is True
    assert userprovided.hashing.hash_available('blake2s', True) is True
    # Non-existent algorithm
    assert userprovided.hashing.hash_available('NonExistentHash', True) is False

testfile_sha224 = '0808f64e60d58979fcb676c96ec938270dea42445aeefcd3a4e6f8db'
testfile_sha256 = '2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae'
testfile_sha512 = 'f7fbba6e0636f890e56fbbf3283e524c6fa3204ae298382d624741d0dc6638326e282c41be5e4254d8820772c5518a2c5a8c0c7f7eda19594a7eb539453e1ed7'

def test_calculate_file_hash():
    # Path is non-existent:
    with pytest.raises(FileNotFoundError):
        userprovided.hashing.calculate_file_hash('some/random/string/qwertzuiopü',
                                              'sha256')
    # Deprecated hash methods:
    with pytest.raises(userprovided.err.DeprecatedHashAlgorithm):
        userprovided.hashing.calculate_file_hash(pathlib.Path('.'), 'md5')
    with pytest.raises(userprovided.err.DeprecatedHashAlgorithm):
        userprovided.hashing.calculate_file_hash(pathlib.Path('.'), 'sha1')
    with pytest.raises(userprovided.err.DeprecatedHashAlgorithm):
        userprovided.hashing.calculate_file_hash(pathlib.Path('.'), 'md5-sha1')
    # Non Existent hash method:
    with pytest.raises(ValueError):
        userprovided.hashing.calculate_file_hash(pathlib.Path('.'),
                                              'non-existent-hash')
    # Default is fallback to SHA256
    assert userprovided.hashing.calculate_file_hash(pathlib.Path('testfile')) == testfile_sha256
    assert userprovided.hashing.calculate_file_hash(pathlib.Path('testfile'), 'sha256') == testfile_sha256
    # SHA224
    assert userprovided.hashing.calculate_file_hash(pathlib.Path('testfile'), 'sha224') == testfile_sha224
    # SHA512
    assert userprovided.hashing.calculate_file_hash(pathlib.Path('testfile'), 'sha512') == testfile_sha512
    # SHA384 (now supported with dynamic algorithm selection)
    result_sha384 = userprovided.hashing.calculate_file_hash(pathlib.Path('testfile'), 'sha384')
    assert len(result_sha384) == 96  # SHA384 produces 96-char hex string
    # SHA3-256 (guaranteed in Python 3.10+)
    result_sha3_256 = userprovided.hashing.calculate_file_hash(pathlib.Path('testfile'), 'sha3_256')
    assert len(result_sha3_256) == 64  # SHA3-256 produces 64-char hex string
    # BLAKE2b (guaranteed in Python 3.10+)
    result_blake2b = userprovided.hashing.calculate_file_hash(pathlib.Path('testfile'), 'blake2b')
    assert len(result_blake2b) == 128  # BLAKE2b produces 128-char hex string


def test_calculate_file_hash_with_expected_value():
    # expected and calculated hash match:
    assert userprovided.hashing.calculate_file_hash(pathlib.Path('testfile'), 'sha512', testfile_sha512) == testfile_sha512
    # expected and calculated hash DO NOT match:
    with pytest.raises(ValueError):
        assert userprovided.hashing.calculate_file_hash(pathlib.Path('testfile'), 'sha512', 'foo') == testfile_sha512

# mock a PermissionError exception
# see: https://stackoverflow.com/questions/1289894/#answer-34677735
def test_calculate_file_hash_mocked_permission():
    with patch('builtins.open', side_effect=PermissionError):
        with pytest.raises(PermissionError) as excinfo:
            userprovided.hashing.calculate_file_hash('testfile')
            assert "insufficient permissions" in str(excinfo.value)


def test_calculate_file_hash_hashlib_error():
    # Test exception handling when hashlib.new raises ValueError
    # This shouldn't normally happen as hash_available checks first,
    # but tests the fallback error handling
    with patch('hashlib.new', side_effect=ValueError('Invalid hash')):
        with pytest.raises(ValueError, match='Hash method sha256 not supported'):
            userprovided.hashing.calculate_file_hash('testfile', 'sha256')


def test_calculate_string_hash():
    # Test basic functionality
    test_data = "hello"
    result = userprovided.hashing.calculate_string_hash(test_data)
    assert len(result) == 64  # SHA256 produces 64-char hex string
    assert result == '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824'

    # Test with different SHA-2 hash methods
    sha224_result = userprovided.hashing.calculate_string_hash(test_data, 'sha224')
    assert len(sha224_result) == 56  # SHA224 produces 56-char hex string

    sha384_result = userprovided.hashing.calculate_string_hash(test_data, 'sha384')
    assert len(sha384_result) == 96  # SHA384 produces 96-char hex string

    sha512_result = userprovided.hashing.calculate_string_hash(test_data, 'sha512')
    assert len(sha512_result) == 128  # SHA512 produces 128-char hex string

    # Test with SHA-3 hash methods (guaranteed in Python 3.10+)
    sha3_256_result = userprovided.hashing.calculate_string_hash(test_data, 'sha3_256')
    assert len(sha3_256_result) == 64  # SHA3-256 produces 64-char hex string

    sha3_512_result = userprovided.hashing.calculate_string_hash(test_data, 'sha3_512')
    assert len(sha3_512_result) == 128  # SHA3-512 produces 128-char hex string

    # Test with BLAKE2 hash methods (guaranteed in Python 3.10+)
    blake2b_result = userprovided.hashing.calculate_string_hash(test_data, 'blake2b')
    assert len(blake2b_result) == 128  # BLAKE2b produces 128-char hex string

    blake2s_result = userprovided.hashing.calculate_string_hash(test_data, 'blake2s')
    assert len(blake2s_result) == 64  # BLAKE2s produces 64-char hex string

    # Test with salt
    salted_result = userprovided.hashing.calculate_string_hash(test_data, salt="mysalt")
    assert salted_result != result  # Should be different with salt

    # Test consistency - same input should produce same output
    result2 = userprovided.hashing.calculate_string_hash(test_data)
    assert result == result2

    # Test with salt consistency
    salted_result2 = userprovided.hashing.calculate_string_hash(test_data, salt="mysalt")
    assert salted_result == salted_result2


def test_calculate_string_hash_errors():
    # Test deprecated hash methods
    with pytest.raises(userprovided.err.DeprecatedHashAlgorithm):
        userprovided.hashing.calculate_string_hash("test", hash_method="md5")

    with pytest.raises(userprovided.err.DeprecatedHashAlgorithm):
        userprovided.hashing.calculate_string_hash("test", hash_method="sha1")

    with pytest.raises(userprovided.err.DeprecatedHashAlgorithm):
        userprovided.hashing.calculate_string_hash("test", hash_method="md5-sha1")

    # Test non-string data
    with pytest.raises(TypeError):
        userprovided.hashing.calculate_string_hash(123)

    with pytest.raises(TypeError):
        userprovided.hashing.calculate_string_hash(None)

    # Test empty string
    with pytest.raises(ValueError):
        userprovided.hashing.calculate_string_hash("")

    # Test non-string salt
    with pytest.raises(TypeError):
        userprovided.hashing.calculate_string_hash("test", salt=123)

    # Test non-existent hash method
    with pytest.raises(ValueError):
        userprovided.hashing.calculate_string_hash("test", hash_method="nonexistent")


def test_calculate_string_hash_encoding():
    # Test different encodings
    unicode_data = "héllo"
    result_utf8 = userprovided.hashing.calculate_string_hash(unicode_data, encoding='utf-8')
    result_latin1 = userprovided.hashing.calculate_string_hash(unicode_data, encoding='latin-1')

    # Different encodings should produce different hashes for unicode chars
    assert result_utf8 != result_latin1

    # Test invalid encoding
    with pytest.raises(UnicodeEncodeError):
        userprovided.hashing.calculate_string_hash("héllo", encoding='ascii')


def test_calculate_string_hash_hashlib_error():
    # Test exception handling when hashlib.new raises ValueError
    # This shouldn't normally happen as hash_available checks first,
    # but tests the fallback error handling
    with patch('hashlib.new', side_effect=ValueError('Invalid hash')):
        with pytest.raises(ValueError, match='Hash method sha256 not supported'):
            userprovided.hashing.calculate_string_hash('test', 'sha256')


def test_calculate_string_hash_generic_exception():
    # Test generic exception handler by mocking hash update to raise unexpected error
    # The generic exception handler catches and re-raises unexpected exceptions
    with patch('hashlib.new') as mock_hash:
        mock_hash_obj = mock_hash.return_value
        mock_hash_obj.update.side_effect = RuntimeError('Unexpected error')
        with pytest.raises(RuntimeError):
            userprovided.hashing.calculate_string_hash('test')


def test_hash_is_deprecated():
    # Test the private helper function through public interface
    # Deprecated algorithms
    assert userprovided.hashing._hash_is_deprecated('md5') is True
    assert userprovided.hashing._hash_is_deprecated('MD5') is True  # Case insensitive
    assert userprovided.hashing._hash_is_deprecated('sha1') is True
    assert userprovided.hashing._hash_is_deprecated('SHA1') is True  # Case insensitive
    assert userprovided.hashing._hash_is_deprecated('md5-sha1') is True
    assert userprovided.hashing._hash_is_deprecated('MD5-SHA1') is True  # Case insensitive
    # Secure algorithms
    assert userprovided.hashing._hash_is_deprecated('sha224') is False
    assert userprovided.hashing._hash_is_deprecated('sha256') is False
    assert userprovided.hashing._hash_is_deprecated('sha384') is False
    assert userprovided.hashing._hash_is_deprecated('sha512') is False
    assert userprovided.hashing._hash_is_deprecated('sha3_256') is False
    assert userprovided.hashing._hash_is_deprecated('blake2b') is False


@pytest.mark.parametrize("mail_address,truth_value", [
    # valid addresses:
    ('test@example.com', True),
    ('test@example-example.com', True),
    ('test@example.co.uk', True),
    ('  test@example.com  ', True),
    ('test+filter@example.com', True),
    # single character local part:
    ('a@example.com', True),
    ('x@test.org', True),
    # single character domains:
    ('example@x.com', True),
    ('test@a.org', True),
    # valid special characters in local part:
    ('user.name@example.com', True),
    ('user_name@example.com', True),
    ('user-name@example.com', True),
    ('first.last@example.com', True),
    # internationalized domain names (IDN):
    ('test@xn--90ae.com', True),
    ('user@example.xn--node', True),
    ('0@a.xn--90ae', True),
    # invalid addresses - consecutive dots in local part:
    ('test..name@example.com', False),
    ('user...name@example.com', False),
    # invalid addresses - dot at start/end of local part:
    ('.test@example.com', False),
    ('test.@example.com', False),
    ('.test.@example.com', False),
    # invalid addresses - TLD too short (single letter TLDs don't exist):
    ('test@example.c', False),
    ('user@domain.x', False),
    # invalid addresses - domain starts/ends with hyphen:
    ('test@-example.com', False),
    ('test@example-.com', False),
    ('test@exam-ple.com', True),  # hyphen in middle is valid
    # invalid addresses - basic format errors:
    ('@example.com', False),
    ('test@@example.com', False),
    ('test@example.', False),
    ('test@example', False),  # missing TLD
    # multiple @ signs:
    ('user@domain.com@evil.com', False),
    ('test@example@malicious.org', False),
    # extra text after valid email:
    ('test@example.com extra junk', False),
    ('valid@domain.com@another.com', False),
    # missing input:
    ('', False),
    ('   ', False),
    # no @ sign:
    ('testexample.com', False),
    # multiple dots in domain labels:
    ('test@exam..ple.com', False),
    ('test@example..com', False)
])
def test_mail_is_email(mail_address, truth_value):
    assert userprovided.mail.is_email(mail_address) is truth_value


def test_mail_is_email_type_validation():
    # Test that None raises TypeError
    with pytest.raises(TypeError, match="Email address must be a string"):
        userprovided.mail.is_email(None)
    
    # Test that non-string types raise TypeError
    with pytest.raises(TypeError, match="Email address must be a string"):
        userprovided.mail.is_email(123)
    
    with pytest.raises(TypeError, match="Email address must be a string"):
        userprovided.mail.is_email(['not', 'a', 'string'])


@settings(max_examples=1000,
          suppress_health_check=[HealthCheck.too_slow])
@given(x=emails())
def test_hypothesis_mail_is_email(x):
    assert userprovided.mail.is_email(x) is True


@pytest.mark.parametrize("bucket_name,truth_value", [
    ('abc', True),
    # perfectly fine at max length:
    ('iekoht9choofe9eixeeseizoo0iuzos1ibeepae7phee3aeghai7shal9kiepiy', True),
    # too short:
    ('ab', False),
    # too long:
    ('iekoht9choofe9eixeeseizoo0iuzos1ibeepae7phee3aeghaif7shal9kiepiy', False),
    # IPv4:
    ('127.0.0.1', False),
    # invalid characters:
    ('iekoht9choofe9ei_xeeseizo', False),
    ('iekoh#xeeseizo', False),
    ('ab$$c', False),
    ('ABc', False),
    # bucket name must start with lowercase letter or number:
    ('-abc', False),
    # containing dots:
    ('iekoht9choofe.eixeeseizoo0iuzos1ibee.pae7ph', True),
    # edge cases - cannot start with dot or hyphen:
    ('.abc', False),
    ('.test-bucket', False),
    # edge cases - cannot end with dot or hyphen:
    ('abc.', False),
    ('test-bucket.', False),
    ('valid-bucket-', False),
    # edge cases - consecutive dots and invalid patterns:
    ('a..b', False),
    ('test..bucket', False),
    ('a.-b', False),
    ('-a.b', False),  # label starts with hyphen
    ('a-.b', False),  # label ends with hyphen
    # single character labels are valid per AWS rules:
    ('a.b', True),
    ('x.y.z', True),
    ('1.a', True),
    ('a.1', True),
    ('a.test', True),
    # forbidden prefixes:
    ('xn--bucket', False),
    ('xn--test-example', False),
    ('sthree-bucket', False),
    ('sthree-example-name', False),
    ('amzn-s3-demo-bucket', False),
    ('amzn-s3-demo-test', False),
    # valid names that contain but don't start with forbidden prefixes:
    ('my-xn--bucket', True),
    ('test-sthree-bucket', True),
    ('my-amzn-s3-demo-bucket', True),
    # forbidden suffixes:
    ('bucket-s3alias', False),
    ('test-bucket-s3alias', False),
    ('bucket--ol-s3', False),
    ('test--ol-s3', False),
    ('bucket.mrap', False),
    ('test.mrap', False),
    ('bucket--x-s3', False),
    ('test--x-s3', False),
    ('bucket--table-s3', False),
    ('test--table-s3', False),
    # valid names that contain but don't end with forbidden suffixes:
    ('s3alias-bucket', True),
    ('ol-s3-test', True),
    ('mrap-bucket', True),
    ('x-s3-test', True),
    ('table-s3-bucket', True)
])
def test_cloud_is_aws_s3_bucket_name(bucket_name, truth_value):
    assert userprovided.parameters.is_aws_s3_bucket_name(bucket_name) is truth_value


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
    with pytest.raises(userprovided.err.QueryKeyConflict):
        userprovided.url.normalize_query_part('foo=foo&foo=bar')
    # Duplicate key in query part of URL with the same value:
    assert userprovided.url.normalize_query_part('foo=bar&foo=bar') == 'foo=bar'
    # Chunk of query is malformed: the = is missing:
    assert userprovided.url.normalize_query_part('missingequalsign&foo=bar') == 'foo=bar'
    assert userprovided.url.normalize_query_part('foo=bar&missingequalsign&') == 'foo=bar'
    # Drop specific key (with tuple, list and set):
    assert userprovided.url.normalize_query_part('foo=1&bar=2&', drop_keys=('bar')) == 'foo=1'
    assert userprovided.url.normalize_query_part('foo=1&bar=2&', drop_keys=['bar']) == 'foo=1'
    assert userprovided.url.normalize_query_part('foo=1&bar=2&', drop_keys={'bar'}) == 'foo=1'
    # Try to drop non-existent key:
    assert userprovided.url.normalize_query_part('foo=1&bar=2&', drop_keys=['not_in_url']) == 'bar=2&foo=1'
    # drop_key is set, but empty or None:
    assert userprovided.url.normalize_query_part('foo=1&bar=2&', drop_keys=[]) == 'bar=2&foo=1'
    assert userprovided.url.normalize_query_part('foo=1&bar=2&', drop_keys=None) == 'bar=2&foo=1'
    # Multiple = signs in parameter values (preserve full value):
    assert userprovided.url.normalize_query_part('token=eyJuYW1lIjoiSm9obiJ9==') == 'token=eyJuYW1lIjoiSm9obiJ9=='
    assert userprovided.url.normalize_query_part('redirect=https://site.com?param=value') == 'redirect=https://site.com?param=value'
    assert userprovided.url.normalize_query_part('formula=x=2*y+3') == 'formula=x=2*y+3'
    assert userprovided.url.normalize_query_part('token=abc=def&name=john') == 'name=john&token=abc=def'


@pytest.mark.parametrize("test_url,normalized_url", [
    # remove whitespace around the URL:
    (' https://www.example.com/ ', 'https://www.example.com/'),
    # Convert scheme and hostname to lowercase
    ('HTTPS://www.ExAmPlE.com', 'https://www.example.com'),
    # Remove standard port for scheme (http)
    ('http://www.example.com:80', 'http://www.example.com'),
    # Remove standard port for scheme (https)
    ('https://www.example.com:443', 'https://www.example.com'),
    # Keep non-standard port for scheme (http)
    ('https://www.example.com:123', 'https://www.example.com:123'),
    # Remove duplicate slashes from the path (1)
    ('https://www.example.com//index.html',
     'https://www.example.com/index.html'),
    # Remove duplicate slashes from the path (2)
    ('https://www.example.com/en//index.html',
     'https://www.example.com/en/index.html'),
    # remove fragment when query is not present
    (' https://www.example.com/index.html#test ',
     'https://www.example.com/index.html'),
    # remove fragment when query is present
    (' https://www.example.com/index.php?name=foo#test ',
     'https://www.example.com/index.php?name=foo'),
    # remove fragment when path is not present
    (' https://www.example.com/#test ', 'https://www.example.com/'),
    # Ignore empty query
    ('https://www.example.com/index.php?',
     'https://www.example.com/index.php'),
    # remove empty elements of the query part
    ('https://www.example.com/index.php?name=foo&example=',
     'https://www.example.com/index.php?name=foo'),
    # order the elements in the query part by alphabet
    ('https://www.example.com/index.py?c=3&a=1&b=2',
     'https://www.example.com/index.py?a=1&b=2&c=3'),
    # URL with non standard query part (does not follow key=value syntax).
    # Mentioned in RFC 3986 as "erroneous" because it mixes query and path.
    # However still used by some software.
    ('https://www.example.com/forums/forumdisplay.php?example-forum',
     'https://www.example.com/forums/forumdisplay.php?example-forum'),
    # Empty query, but '?' indicating one
    ('https://www.example.com/index.php?', 'https://www.example.com/index.php')
])
def test_normalize_url(test_url, normalized_url):
    assert userprovided.url.normalize_url(test_url) == normalized_url


def test_normalize_url_exceptions():
    # input is not an URL
    with pytest.raises(ValueError):
        userprovided.url.normalize_url('somestring')
    # Contradiction: drop keys, but query part shall be unchanged
    with pytest.raises(userprovided.err.ContradictoryParameters):
        userprovided.url.normalize_url(
            'https://www.example.com/index.php?id=1',
            ['id'],
            do_not_change_query_part = True)


def test_normalize_url_removing_keys():
    # The function just hands over drop_keys to normalize_query_part, so
    # more cases are tested in test_normalize_query_part() above and this
    # just ensures the parameter is passed on.
    assert userprovided.url.normalize_url(
        'https://www.example.com/index.py?c=3&a=1&b=2',
        drop_keys=['c']) == 'https://www.example.com/index.py?a=1&b=2'


def test_normalize_url_unchanged_query():
    assert userprovided.url.normalize_url(
        '  https://www.example.com/index.php?foo=1&foo=2',
        [],
        do_not_change_query_part = True
    ) == 'https://www.example.com/index.php?foo=1&foo=2'


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


def test_is_shortened_url():
    # Test known shortening services
    assert userprovided.url.is_shortened_url('https://bit.ly/abc123') is True
    assert userprovided.url.is_shortened_url('https://tinyurl.com/xyz789') is True
    assert userprovided.url.is_shortened_url('https://t.co/abcdef') is True
    assert userprovided.url.is_shortened_url('https://goo.gl/maps123') is True
    assert userprovided.url.is_shortened_url('https://lnkd.in/xyz') is True

    # Test with www prefix
    assert userprovided.url.is_shortened_url('https://www.bit.ly/abc123') is True
    assert userprovided.url.is_shortened_url('https://www.tinyurl.com/xyz789') is True

    # Test case insensitivity
    assert userprovided.url.is_shortened_url('https://BIT.LY/abc123') is True
    assert userprovided.url.is_shortened_url('https://TINYURL.COM/xyz789') is True

    # Test non-shortened URLs
    assert userprovided.url.is_shortened_url('https://example.com/page') is False
    assert userprovided.url.is_shortened_url('https://google.com/search') is False
    assert userprovided.url.is_shortened_url('https://github.com/user/repo') is False

    # Test invalid URLs
    assert userprovided.url.is_shortened_url('not-a-url') is False
    assert userprovided.url.is_shortened_url('') is False
    assert userprovided.url.is_shortened_url('ftp://bit.ly/test') is True  # Valid URL with shortener domain

    # Test edge cases
    assert userprovided.url.is_shortened_url('https://bit.ly') is True  # No path
    assert userprovided.url.is_shortened_url('http://tinyurl.com/') is True  # HTTP

    # Test some enterprise/business shorteners
    assert userprovided.url.is_shortened_url('https://rebrand.ly/custom') is True
    assert userprovided.url.is_shortened_url('https://short.link/test') is True
    assert userprovided.url.is_shortened_url('https://cutt.ly/example') is True


def test_is_shortened_url_exception_handling():
    # Test exception handling in is_shortened_url when urlparse throws unexpected error
    # Need to patch where it's used in the url module
    with patch('userprovided.url.urllib.parse.urlparse') as mock_parse:
        # Make is_url succeed but then fail in is_shortened_url
        mock_parse.side_effect = [
            type('obj', (object,), {'scheme': 'https', 'netloc': 'bit.ly'})(),  # First call in is_url
            Exception('Unexpected error')  # Second call in is_shortened_url
        ]
        # Should return False and not raise
        assert userprovided.url.is_shortened_url('https://bit.ly/test') is False


def test_is_valid_coordinates():
    # Valid coordinates - major cities
    assert userprovided.geo.is_valid_coordinates(40.7128, -74.0060) is True  # New York City
    assert userprovided.geo.is_valid_coordinates(51.5074, -0.1278) is True   # London
    assert userprovided.geo.is_valid_coordinates(-33.8688, 151.2093) is True # Sydney
    assert userprovided.geo.is_valid_coordinates(35.6762, 139.6503) is True  # Tokyo
    
    # Valid coordinates - extremes
    assert userprovided.geo.is_valid_coordinates(90.0, 180.0) is True   # North Pole, Date Line
    assert userprovided.geo.is_valid_coordinates(-90.0, -180.0) is True # South Pole, Date Line
    assert userprovided.geo.is_valid_coordinates(0.0, 0.0) is True      # Equator, Prime Meridian
    
    # Valid coordinates - string inputs
    assert userprovided.geo.is_valid_coordinates('40.7128', '-74.0060') is True
    assert userprovided.geo.is_valid_coordinates('0', '0') is True
    
    # Valid coordinates - integer inputs
    assert userprovided.geo.is_valid_coordinates(45, 90) is True
    assert userprovided.geo.is_valid_coordinates(-45, -90) is True
    
    # Invalid latitude - out of range
    assert userprovided.geo.is_valid_coordinates(91.0, 0.0) is False    # > 90
    assert userprovided.geo.is_valid_coordinates(-91.0, 0.0) is False   # < -90
    assert userprovided.geo.is_valid_coordinates(90.1, 0.0) is False    # Just over 90
    assert userprovided.geo.is_valid_coordinates(-90.1, 0.0) is False   # Just under -90
    
    # Invalid longitude - out of range
    assert userprovided.geo.is_valid_coordinates(0.0, 181.0) is False   # > 180
    assert userprovided.geo.is_valid_coordinates(0.0, -181.0) is False  # < -180
    assert userprovided.geo.is_valid_coordinates(0.0, 180.1) is False   # Just over 180
    assert userprovided.geo.is_valid_coordinates(0.0, -180.1) is False  # Just under -180
    
    # Invalid format inputs
    assert userprovided.geo.is_valid_coordinates('invalid', '0') is False
    assert userprovided.geo.is_valid_coordinates('0', 'invalid') is False
    assert userprovided.geo.is_valid_coordinates('abc', 'def') is False
    assert userprovided.geo.is_valid_coordinates(None, 0) is False
    assert userprovided.geo.is_valid_coordinates(0, None) is False
    assert userprovided.geo.is_valid_coordinates('', '') is False
    
    # Edge case - very precise coordinates
    assert userprovided.geo.is_valid_coordinates(89.9999999, 179.9999999) is True
    assert userprovided.geo.is_valid_coordinates(-89.9999999, -179.9999999) is True
    
    # Test boolean rejection (bool is subclass of int)
    assert userprovided.geo.is_valid_coordinates(True, False) is False
    assert userprovided.geo.is_valid_coordinates(False, True) is False
    assert userprovided.geo.is_valid_coordinates(True, 90.0) is False
    assert userprovided.geo.is_valid_coordinates(45.0, False) is False
    
    # Test non-finite values (NaN, Infinity)
    assert userprovided.geo.is_valid_coordinates(float('nan'), 0.0) is False
    assert userprovided.geo.is_valid_coordinates(0.0, float('nan')) is False
    assert userprovided.geo.is_valid_coordinates(float('inf'), 0.0) is False
    assert userprovided.geo.is_valid_coordinates(0.0, float('-inf')) is False


# There are some edge cases in which `mimetypes.guess_extension`
# (in the python standard library) has different return values
# depending on the Python version used.
def test_determine_file_extension_version_inconsistencies():
    with patch('mimetypes.guess_extension', return_value='.bat'):
        assert userprovided.url.determine_file_extension('https://www.example.com/test.txt', 'text/plain') == '.txt'
    with patch('mimetypes.guess_extension', return_value='.htm'):
        assert userprovided.url.determine_file_extension('https://www.example.com/test.htm', 'text/plain') == '.html'
    with patch('mimetypes.guess_extension', return_value=None):
        assert userprovided.url.determine_file_extension('https://www.example.com/test.htm', 'text/plain') == '.unknown'


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


def test_parameters_is_port():
    assert userprovided.parameters.is_port(443) is True
    assert userprovided.parameters.is_port(65536) is False
    assert userprovided.parameters.is_port(-1) is False
    with pytest.raises(ValueError):
        userprovided.parameters.is_port('foo')
    with pytest.raises(ValueError):
        userprovided.parameters.is_port(None)


@pytest.mark.parametrize("input,expected", [
    # single string with multiple characters
    # (wrong would be turning each character into an element)
    ('abc', {'abc'}),
    # list with duplicates to set:
    (['a', 'a', 'b', 'c'], {'a', 'b', 'c'}),
    # tuple with duplicates:
    (('a', 'a', 'b', 'c'), {'a', 'b', 'c'}),
    # a set should return unchanged:
    ({'a', 'b', 'c'}, {'a', 'b', 'c'})
])
def test_convert_to_set(input, expected):
    assert userprovided.parameters.convert_to_set(input) == expected


def test_convert_to_set_exceptions():
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


@pytest.mark.parametrize("dict_to_check,truth_value", [
    # valid input:
    ({'a': 'foo', 'b': 'example', 'c': 'foo'}, True),
    ({'a': 'foo', 'b': 'example', 'c': {'foo': 'foo'}}, True),
    ({'a': 'foo', 'b': 'example', 'c': [1, 2, 3]}, True),
    ({'a': 'foo', 'b': 'example', 'c': (1, 2, 3)}, True),
    ({'a': 'foo', 'b': 'example', 'c': {1, 2, 3}}, True),
    ({'a': 1, 'b': 2, 'c': 3}, True),
    # Some key is None:
    ({'a': 1, 'b': 2, 'c': None}, False),
    # Keys with empty value:
    ({'a': 1, 'b': 2, 'c': ''}, False),
    ({'a': 1, 'b': 2, 'c': '      '}, False),
    ({'a': 1, 'b': 2, 'c': '\t'}, False),
    ({'a': 1, 'b': 2, 'c': str()}, False),
    ({'a': 1, 'b': 2, 'c': list()}, False),
    ({'a': 1, 'b': 2, 'c': tuple()}, False),
    ({'a': 1, 'b': 2, 'c': dict()}, False)
    ])
def test_keys_neither_none_nor_empty(
    dict_to_check: dict, truth_value: bool):
    assert userprovided.parameters.keys_neither_none_nor_empty(dict_to_check) is truth_value

def test_keys_neither_none_nor_empty_false_input():
    # not a dictionary
    with pytest.raises(ValueError):
        userprovided.parameters.keys_neither_none_nor_empty('foo')
    # empty dictionary
    with pytest.raises(ValueError):
        userprovided.parameters.keys_neither_none_nor_empty(dict())

def test_numeric_in_range():
    # Minimum value larger than maximum value
    with pytest.raises(userprovided.err.ContradictoryParameters):
        userprovided.parameters.numeric_in_range(
            'example',
            101,
            100,
            1.0,
            50)

    # Fallback value outside the allowed range
    with pytest.raises(userprovided.err.ContradictoryParameters):
        userprovided.parameters.numeric_in_range(
            'example',
            101,
            100,
            200,
            5000  # fallback larger than maximum
            )
    with pytest.raises(userprovided.err.ContradictoryParameters):
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
    with pytest.raises(userprovided.err.ContradictoryParameters):
        userprovided.parameters.string_in_range('example', 10, 5)
    # not a string - test TypeError
    with pytest.raises(TypeError):
        userprovided.parameters.string_in_range(123, 1, 5)
    with pytest.raises(TypeError):
        userprovided.parameters.string_in_range(None, 1, 5)


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
