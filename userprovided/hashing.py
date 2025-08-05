#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hash functionality for the userprovided library
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
(c) 2020-2025 Rüdiger Voigt
Released under the Apache License 2.0
"""


import hashlib
import logging
import pathlib
from typing import Optional, Union

from userprovided import err


def _hash_is_deprecated(hash_method: str) -> bool:
    """Checks if a hash algorithm is deprecated for security reasons.

    Args:
        hash_method: Name of the hash algorithm to check.

    Returns:
        True if the hash method is deprecated, False otherwise.
    """
    deprecated_algorithms = {'md5', 'sha1'}
    return hash_method.lower() in deprecated_algorithms


def hash_available(hash_method: str,
                   fail_on_deprecated: bool = True) -> bool:
    """Checks if a hashing algorithm is available on the system.

    Validates whether the specified hash algorithm is supported by the
    system's hashlib implementation. Can optionally reject deprecated
    algorithms for security reasons.

    Args:
        hash_method: Name of the hash algorithm to check (e.g., 'sha256').
        fail_on_deprecated: If True, raises exception for deprecated algorithms
            like MD5 and SHA1. Defaults to True.

    Returns:
        True if the hash method is available and allowed, False otherwise.

    Raises:
        ValueError: If no hash method is provided or empty string given.
        DeprecatedHashAlgorithm: If hash_method is deprecated and
            fail_on_deprecated is True.
    """

    if hash_method:
        hash_method = hash_method.strip()

    if hash_method == '' or hash_method is None:
        raise ValueError('No hash method provided')

    # Is the chosen method available and supported?

    if fail_on_deprecated:
        if _hash_is_deprecated(hash_method):
            raise err.DeprecatedHashAlgorithm('The supplied hash method %s is deprecated!', hash_method)

    if hash_method in hashlib.algorithms_available:
        logging.debug('Hash method %s is available.', hash_method)
        return True
    return False


def calculate_file_hash(file_path: Union[pathlib.Path, str],
                        hash_method: str = 'sha256',
                        expected_hash: Optional[str] = None) -> str:
    """Calculates cryptographic hash of a file.

    Computes the hash digest of a file using the specified algorithm.
    Optionally verifies the calculated hash against an expected value
    to detect file modifications or corruption.

    Args:
        file_path: Path to the file to hash. Can be string or Path object.
        hash_method: Hash algorithm to use. Supported: 'sha224', 'sha256',
            'sha512'. Defaults to 'sha256'.
        expected_hash: Expected hash value for verification. If provided
            and doesn't match calculated hash, raises ValueError.
            Defaults to None.

    Returns:
        Hexadecimal string representation of the file's hash digest.

    Raises:
        DeprecatedHashAlgorithm: If hash_method is MD5 or SHA1.
        ValueError: If hash method is not supported or calculated hash
            doesn't match expected_hash.
        FileNotFoundError: If the specified file doesn't exist.
        PermissionError: If insufficient permissions to read the file.
    """

    if _hash_is_deprecated(hash_method):
        raise err.DeprecatedHashAlgorithm(
            'Deprecated hash method not supported')

    if hash_available(hash_method):
        if hash_method == 'sha224':
            h = hashlib.sha224()
        elif hash_method == 'sha256':
            h = hashlib.sha256()
        elif hash_method == 'sha512':
            h = hashlib.sha512()
        else:
            raise ValueError('Hash method not supported')
    else:
        raise ValueError(f"Hash method {hash_method} not available on system.")

    try:
        with open(pathlib.Path(file_path), 'rb') as file:
            content = file.read()
        h.update(content)
        calculated_hash = h.hexdigest()
        if expected_hash and expected_hash != calculated_hash:
            mismatch_message = ("Mismatch between calculated and expected " +
                                f"{hash_method} hash for {file_path}")
            logging.exception(mismatch_message)
            raise ValueError(mismatch_message)
        return calculated_hash
    except FileNotFoundError:
        logging.exception(
            'Cannot calculate hash: File not found or not readable.',
            exc_info=True)
        raise
    except PermissionError:
        logging.exception(
            'Cannot calculate file hash: insufficient permissions.',
            exc_info=True)
        raise
    except Exception:
        logging.error('Exception while trying to get file hash',
                      exc_info=True)
        raise


def calculate_string_hash(data: str,
                          hash_method: str = 'sha256',
                          salt: Optional[str] = None,
                          encoding: str = 'utf-8') -> str:
    """Calculates cryptographic hash of string data.

    Computes the hash digest of string data using the specified algorithm.
    Optionally adds salt for enhanced security against rainbow table attacks.
    Always uses secure hash algorithms.

    Args:
        data: String data to hash.
        hash_method: Hash algorithm to use. Supported: 'sha224', 'sha256',
            'sha512'. Defaults to 'sha256'.
        salt: Optional salt string to append to data before hashing.
            Strongly recommended for password hashing. Defaults to None.
        encoding: Text encoding to use when converting string to bytes.
            Defaults to 'utf-8'.

    Returns:
        Hexadecimal string representation of the hash digest.

    Raises:
        DeprecatedHashAlgorithm: If hash_method is MD5 or SHA1.
        ValueError: If hash method is not supported or data is empty.
        TypeError: If data is not a string.
        UnicodeEncodeError: If data cannot be encoded with specified encoding.
    """
    if not isinstance(data, str):
        raise TypeError('Data must be a string')

    if not data:
        raise ValueError('Cannot hash empty string')

    if _hash_is_deprecated(hash_method):
        raise err.DeprecatedHashAlgorithm(
            'Deprecated hash method not supported')

    if not hash_available(hash_method):
        raise ValueError(f"Hash method {hash_method} not available on "
                         "system.")

    # Prepare data for hashing
    if salt:
        if not isinstance(salt, str):
            raise TypeError('Salt must be a string')
        data_to_hash = data + salt
        logging.debug('Salt added to data for hashing')
    else:
        data_to_hash = data
        logging.warning('No salt provided - consider using salt for '
                        'enhanced security')

    try:
        # Convert string to bytes using specified encoding
        byte_data = data_to_hash.encode(encoding)

        # Create hash object
        if hash_method == 'sha224':
            h = hashlib.sha224()
        elif hash_method == 'sha256':
            h = hashlib.sha256()
        elif hash_method == 'sha512':
            h = hashlib.sha512()
        else:
            raise ValueError('Hash method not supported')

        h.update(byte_data)
        calculated_hash = h.hexdigest()

        logging.debug('String hash calculated successfully using %s',
                      hash_method)
        return calculated_hash

    except UnicodeEncodeError:
        logging.exception('Cannot encode string with %s encoding', encoding)
        raise
    except Exception:
        logging.error('Exception while calculating string hash',
                      exc_info=True)
        raise

