"""
Tests for the hashing module of userprovided.
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
Released under the Apache License 2.0
"""

# ruff: noqa

from unittest.mock import patch
import pathlib

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
    # Deprecated algorithm with fail_on_deprecated=False: available but not rejected
    assert userprovided.hashing.hash_available('md5', False) is True

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
    assert userprovided.hashing.calculate_file_hash(pathlib.Path('tests/testfile')) == testfile_sha256
    assert userprovided.hashing.calculate_file_hash(pathlib.Path('tests/testfile'), 'sha256') == testfile_sha256
    # SHA224
    assert userprovided.hashing.calculate_file_hash(pathlib.Path('tests/testfile'), 'sha224') == testfile_sha224
    # SHA512
    assert userprovided.hashing.calculate_file_hash(pathlib.Path('tests/testfile'), 'sha512') == testfile_sha512
    # SHA384 (now supported with dynamic algorithm selection)
    result_sha384 = userprovided.hashing.calculate_file_hash(pathlib.Path('tests/testfile'), 'sha384')
    assert len(result_sha384) == 96  # SHA384 produces 96-char hex string
    # SHA3-256 (guaranteed in Python 3.10+)
    result_sha3_256 = userprovided.hashing.calculate_file_hash(pathlib.Path('tests/testfile'), 'sha3_256')
    assert len(result_sha3_256) == 64  # SHA3-256 produces 64-char hex string
    # BLAKE2b (guaranteed in Python 3.10+)
    result_blake2b = userprovided.hashing.calculate_file_hash(pathlib.Path('tests/testfile'), 'blake2b')
    assert len(result_blake2b) == 128  # BLAKE2b produces 128-char hex string


def test_calculate_file_hash_with_expected_value():
    # expected and calculated hash match:
    assert userprovided.hashing.calculate_file_hash(pathlib.Path('tests/testfile'), 'sha512', testfile_sha512) == testfile_sha512
    # expected and calculated hash DO NOT match:
    with pytest.raises(ValueError):
        assert userprovided.hashing.calculate_file_hash(pathlib.Path('tests/testfile'), 'sha512', 'foo') == testfile_sha512


def test_calculate_file_hash_expected_value_normalized():
    # Hashes are often published uppercase, but hexdigest() is lowercase.
    assert userprovided.hashing.calculate_file_hash(
        pathlib.Path('tests/testfile'), 'sha512',
        testfile_sha512.upper()) == testfile_sha512
    # Surrounding whitespace (i.e. from a config file) is ignored.
    assert userprovided.hashing.calculate_file_hash(
        pathlib.Path('tests/testfile'), 'sha512',
        f"  {testfile_sha512}\n") == testfile_sha512


def test_calculate_file_hash_empty_expected_value():
    # An empty string must NOT skip the verification: a config value left
    # blank would otherwise turn the check into a silent success.
    with pytest.raises(ValueError):
        userprovided.hashing.calculate_file_hash(
            pathlib.Path('tests/testfile'), 'sha512', '')
    # Only None skips the check.
    assert userprovided.hashing.calculate_file_hash(
        pathlib.Path('tests/testfile'), 'sha512', None) == testfile_sha512


def test_calculate_file_hash_mismatch_raises_hash_mismatch():
    """A failed integrity check is separable from a bad algorithm name.

    Both used to be a bare ValueError, so a caller could not tell 'you typo'd
    the algorithm' from 'this file does not match its expected hash'.
    """
    with pytest.raises(userprovided.err.HashMismatch):
        userprovided.hashing.calculate_file_hash(
            pathlib.Path('tests/testfile'), 'sha512', 'foo')
    # An unknown algorithm is a configuration error, not a mismatch:
    with pytest.raises(ValueError) as excinfo:
        userprovided.hashing.calculate_file_hash(
            pathlib.Path('tests/testfile'), 'not_a_hash_method')
    assert not isinstance(excinfo.value, userprovided.err.HashMismatch)


def test_calculate_file_hash_mismatch_still_caught_as_value_error():
    """HashMismatch subclasses ValueError, so old handlers keep working."""
    with pytest.raises(ValueError):
        userprovided.hashing.calculate_file_hash(
            pathlib.Path('tests/testfile'), 'sha512', 'foo')
    with pytest.raises(userprovided.err.UserprovidedException):
        userprovided.hashing.calculate_file_hash(
            pathlib.Path('tests/testfile'), 'sha512', 'foo')


def test_calculate_file_hash_non_ascii_expected_value():
    """A non-ASCII expected hash is a mismatch, not an unrelated TypeError.

    hmac.compare_digest refuses non-ASCII input. A hexdigest is ASCII, so such
    a value simply cannot match and must be reported as a failed check.
    """
    with pytest.raises(userprovided.err.HashMismatch):
        userprovided.hashing.calculate_file_hash(
            pathlib.Path('tests/testfile'), 'sha512', 'ä' * 128)
    # A hash with one non-ASCII character swapped in must not slip through:
    with pytest.raises(userprovided.err.HashMismatch):
        userprovided.hashing.calculate_file_hash(
            pathlib.Path('tests/testfile'), 'sha512',
            testfile_sha512[:-1] + 'ä')


def test_calculate_file_hash_expected_value_wrong_type():
    """A non-string expected_hash is a caller error, not a mismatch."""
    for wrong_type in (123, 1.5, True, [testfile_sha512], b'abc'):
        with pytest.raises(TypeError):
            userprovided.hashing.calculate_file_hash(
                pathlib.Path('tests/testfile'), 'sha512', wrong_type)

# mock a PermissionError exception
# see: https://stackoverflow.com/questions/1289894/#answer-34677735
def test_calculate_file_hash_mocked_permission():
    with patch('builtins.open', side_effect=PermissionError):
        with pytest.raises(PermissionError) as excinfo:
            userprovided.hashing.calculate_file_hash('tests/testfile')
            assert "insufficient permissions" in str(excinfo.value)


def test_calculate_file_hash_alias_bypass():
    # Simulate a platform alias that resolves to a deprecated algorithm.
    # Patch hash_available to let the alias pass the availability check,
    # then verify the post-construction canonical name check catches it.
    with patch('userprovided.hashing.hash_available', return_value=True), \
         patch('hashlib.new') as mock_new:
        mock_hash = mock_new.return_value
        mock_hash.name = 'md5'
        with pytest.raises(userprovided.err.DeprecatedHashAlgorithm,
                           match="resolves to deprecated"):
            userprovided.hashing.calculate_file_hash('tests/testfile','some-alias')


def test_calculate_file_hash_hashlib_error():
    # Test exception handling when hashlib.new raises ValueError
    # This shouldn't normally happen as hash_available checks first,
    # but tests the fallback error handling
    with patch('hashlib.new', side_effect=ValueError('Invalid hash')):
        with pytest.raises(ValueError, match='Hash method sha256 not supported'):
            userprovided.hashing.calculate_file_hash('tests/testfile','sha256')


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

    # Test consistency - same input should produce same output
    result2 = userprovided.hashing.calculate_string_hash(test_data)
    assert result == result2


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


def test_calculate_string_hash_alias_bypass():
    # Simulate a platform alias that resolves to a deprecated algorithm.
    # Patch hash_available to let the alias pass the availability check,
    # then verify the post-construction canonical name check catches it.
    with patch('userprovided.hashing.hash_available', return_value=True), \
         patch('hashlib.new') as mock_new:
        mock_hash = mock_new.return_value
        mock_hash.name = 'sha1'
        with pytest.raises(userprovided.err.DeprecatedHashAlgorithm,
                           match="resolves to deprecated"):
            userprovided.hashing.calculate_string_hash('test', 'some-alias')


def test_calculate_string_hash_hashlib_error():
    # Test exception handling when hashlib.new raises ValueError
    # This shouldn't normally happen as hash_available checks first,
    # but tests the fallback error handling
    with patch('hashlib.new', side_effect=ValueError('Invalid hash')):
        with pytest.raises(ValueError, match='Hash method sha256 not supported'):
            userprovided.hashing.calculate_string_hash('test', 'sha256')


def test_calculate_string_hash_unexpected_error_propagates():
    # An unexpected error from the hash object must reach the caller instead of
    # being swallowed. Mock update() to raise something the function does not
    # anticipate.
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
