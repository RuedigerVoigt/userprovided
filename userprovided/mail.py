#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Checking Email for the userprovided library
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
Copyright (c) 2020-2026 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""

# python standard library:
import logging
import re


# Compiled regex pattern for performance optimization
_EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+"  # Local part start
    r"(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*"  # Local part with dots (no consecutive)
    r"@"  # @
    r"[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?"  # Domain label
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)*"  # More domain labels
    # TLD: min 2 chars; alphanumeric + hyphen for IDN
    r"\.(?:[a-zA-Z0-9]{2,}|[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9])$"
)


def is_email(mailaddress: str) -> bool:
    """Validates if a string has a valid email address format.

    Performs basic regex-based validation to check if the provided string
    follows a valid email address pattern. Supports internationalized domains.

    Args:
        mailaddress: The email address string to validate.

    Returns:
        True if the email address format is valid, False otherwise.

    Raises:
        TypeError: If mailaddress is not a string.
    """

    if not isinstance(mailaddress, str):
        raise TypeError('Email address must be a string')

    if not mailaddress or mailaddress == '':
        logging.debug('No mail address supplied.')
        return False

    mailaddress = mailaddress.strip()

    # RFC 5321: max 254 characters total, max 64 for the local part
    if len(mailaddress) > 254:
        logging.debug('Email address exceeds RFC 5321 maximum of 254 characters.')
        return False
    local_part = mailaddress.split('@')[0]
    if len(local_part) > 64:
        logging.debug('Email local part exceeds RFC 5321 maximum of 64 characters.')
        return False

    if not _EMAIL_PATTERN.match(mailaddress):
        # Use %r, not %s: this is rejected, attacker-controlled input that
        # may contain newlines or control characters. repr() escapes them
        # and prevents log injection / forged log lines.
        logging.debug(
            'The supplied mailaddress %r has an unknown format.', mailaddress)
        return False

    logging.debug('%r seems to have a valid format', mailaddress)
    return True
