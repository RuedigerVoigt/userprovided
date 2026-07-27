#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hash functionality for the userprovided library
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
Copyright (c) 2020-2026 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""


import hashlib
import hmac
import logging
import pathlib

from userprovided import err


def _hash_is_deprecated(hash_method: str) -> bool:
    """Checks if a hash algorithm is deprecated for security reasons.

    Args:
        hash_method: Name of the hash algorithm to check.

    Returns:
        True if the hash method is deprecated, False otherwise.
    """
    deprecated_algorithms = {'md5', 'sha1', 'md5-sha1'}
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

    if not hash_method or not hash_method.strip():
        raise ValueError('No hash method provided')
    hash_method = hash_method.strip()

    # Is the chosen method available and supported?

    if fail_on_deprecated:
        if _hash_is_deprecated(hash_method):
            raise err.DeprecatedHashAlgorithm(
                f'The supplied hash method {hash_method} is deprecated!')

    if hash_method in hashlib.algorithms_available:
        logging.debug('Hash method %s is available.', hash_method)
        return True
    return False


def _new_hash(hash_method: str) -> 'hashlib._Hash':
    """Creates a hash object, rejecting deprecated algorithms.

    Centralizes the guard sequence shared by the public hash functions:
    reject the requested name, check availability, construct the object,
    then re-check its canonical name to catch platform-specific aliases
    (e.g. 'sha' resolving to 'sha1').

    Args:
        hash_method: Name of the hash algorithm to use.

    Returns:
        A new hashlib hash object for the requested algorithm.

    Raises:
        DeprecatedHashAlgorithm: If hash_method is deprecated, or resolves
            to a deprecated algorithm.
        ValueError: If the hash method is not available or not supported.
    """
    if _hash_is_deprecated(hash_method):
        raise err.DeprecatedHashAlgorithm(
            'Deprecated hash method not supported')

    if not hash_available(hash_method):
        raise ValueError(f"Hash method {hash_method} not available on system.")

    try:
        hash_object = hashlib.new(hash_method)
    except ValueError as e:
        raise ValueError(f"Hash method {hash_method} not supported: {e}") from e

    if _hash_is_deprecated(hash_object.name):
        raise err.DeprecatedHashAlgorithm(
            f"Hash method '{hash_method}' resolves to "
            f"deprecated algorithm '{hash_object.name}'")

    return hash_object


def calculate_file_hash(file_path: pathlib.Path | str,
                        hash_method: str = 'sha256',
                        expected_hash: str | None = None) -> str:
    """Calculates cryptographic hash of a file.

    Computes the hash digest of a file using the specified algorithm.
    Optionally verifies the calculated hash against an expected value
    to detect file modifications or corruption.

    Args:
        file_path: Path to the file to hash. Can be string or Path object.
        hash_method: Hash algorithm to use. Supports all algorithms available
            in hashlib (sha224, sha256, sha384, sha512, sha3_*, blake2*, etc.)
            excluding deprecated algorithms (MD5, SHA1). Defaults to 'sha256'.
        expected_hash: Expected hash value for verification. Compared
            case-insensitively and in constant time, ignoring surrounding
            whitespace. A mismatch raises ValueError. Only None skips the
            verification: an empty string is a value that cannot match,
            not a request to skip the check. Defaults to None.

    Returns:
        Hexadecimal string representation of the file's hash digest.

    Raises:
        DeprecatedHashAlgorithm: If hash_method is MD5 or SHA1.
        ValueError: If hash method is not supported or calculated hash
            doesn't match expected_hash.
        FileNotFoundError: If the specified file doesn't exist.
        PermissionError: If insufficient permissions to read the file.

    Note:
        This function does not restrict which files can be hashed. The
        caller is responsible for ensuring file_path points to an
        intended file and does not contain path traversal sequences.
    """

    hash_object = _new_hash(hash_method)

    try:
        with open(pathlib.Path(file_path), 'rb') as file:
            while chunk := file.read(65536):
                hash_object.update(chunk)
    except FileNotFoundError:
        logging.debug(
            'Cannot calculate hash: File not found or not readable.',
            exc_info=True)
        raise
    except PermissionError:
        logging.debug(
            'Cannot calculate file hash: insufficient permissions.',
            exc_info=True)
        raise

    calculated_hash = hash_object.hexdigest()

    if expected_hash is not None:
        # hexdigest() is lowercase, but hashes are often published uppercase.
        # compare_digest keeps the comparison constant-time.
        if not hmac.compare_digest(expected_hash.strip().lower(),
                                   calculated_hash):
            mismatch_message = ("Mismatch between calculated and expected " +
                                f"{hash_method} hash for {file_path}")
            logging.debug(mismatch_message)
            raise ValueError(mismatch_message)

    return calculated_hash


def calculate_string_hash(data: str,
                          hash_method: str = 'sha256',
                          encoding: str = 'utf-8') -> str:
    """Compute a deterministic hash of string data (NOT for security).

    This is a generic hash utility for non-security use cases such as
    fingerprints, cache keys, or content de-duplication.

    Do NOT use it for:
      - Password storage
      - Message integrity/authenticity
      - Anything needing resistance to brute force or active attackers.

    Args:
        data: String data to hash.
        hash_method: Hash algorithm to use. Supports algorithms available in
            `hashlib` (sha224, sha256, sha384, sha512, sha3_*, blake2*, etc.)
            excluding deprecated algorithms (MD5, SHA1). Defaults to 'sha256'.
        encoding: Text encoding to use when converting string to bytes
            (for this helper we only accept text input). Defaults to 'utf-8'.

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

    hash_object = _new_hash(hash_method)

    try:
        byte_data = data.encode(encoding)
    except UnicodeEncodeError:
        logging.debug('Cannot encode string with %s encoding', encoding)
        raise

    hash_object.update(byte_data)
    calculated_hash = hash_object.hexdigest()

    logging.debug('String hash calculated successfully using %s', hash_method)
    return calculated_hash
