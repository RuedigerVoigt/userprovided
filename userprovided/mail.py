#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Checking Email for the userprovided library
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
(c) 2020-2025 Rüdiger Voigt
Released under the Apache License 2.0
"""

# python standard library:
import logging
import re


# Compiled regex pattern for performance optimization
# Improvements: no consecutive dots in local part, no dots at start/end of local part,
# TLD minimum 2 chars (supports IDN with xn-- prefix), domain labels can't start/end with hyphen
_EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+"  # Local part start
    r"(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*"  # Local part with dots (no consecutive)
    r"@"  # @
    r"[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?"  # Domain label
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)*"  # More domain labels
    r"\.(?:[a-zA-Z0-9]{2,}|[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9])$"  # TLD (minimum 2 chars, alphanumeric+hyphen for IDN)
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
        logging.warning('No mail address supplied.')
        return False

    mailaddress = mailaddress.strip()
    if not _EMAIL_PATTERN.match(mailaddress):
        logging.error(
            'The supplied mailaddress %s has an unknown format.', mailaddress)
        return False

    logging.debug('%s seems to have a valid format', mailaddress)
    return True
