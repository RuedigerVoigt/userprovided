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
        if hash_method in ('md5', 'sha1'):
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

    if hash_method in ('md5', 'sha1'):
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
