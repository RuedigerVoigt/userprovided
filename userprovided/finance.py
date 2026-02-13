#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Finance related validation functions
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
Copyright (c) 2020-2026 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""

import logging


def _luhn_check_isin(isin_candidate: str) -> bool:
    """Apply the Luhn algorithm to a 12-character uppercase ISIN.

    This validates the ISIN does not contain a typo, but does not mean
    the ISIN is in use.

    For a description refer to https://en.wikipedia.org/wiki/Luhn_algorithm

    Args:
        isin_candidate: A 12-character uppercase ISIN string. Should already
            be validated for length and character classes with is_isin.

    Returns:
        True if the Luhn checksum is valid (sum mod 10 == 0).
    """
    # Ensure correct format if called from outside is_isin()
    isin_candidate = isin_candidate.strip().upper()

    digits = []
    for ch in isin_candidate:
        if '0' <= ch <= '9':
            digits.append(ch)
        elif 'A' <= ch <= 'Z':
            digits.append(str(ord(ch) - ord('A') + 10))
        else:
            return False

    digit_str = ''.join(digits)

    total = 0
    for i, d in enumerate(reversed(digit_str)):
        n = ord(d) - ord('0')
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n

    return total % 10 == 0


def is_isin(isin_candidate: str) -> bool:
    """Check if a string is has the correct format for an International
    Securities Identification Number (ISIN).

     For a description of the format please refer to:
     * https://en.wikipedia.org/wiki/International_Securities_Identification_Number
     * ISO 6166 as the normative source

     It does NOT check if the ISIN is or was in use. For this you need a data provider.

    An ISIN has exactly 12 characters:
    - Positions 1-2: two letters (ISO 3166-1 alpha-2 country code)
    - Positions 3-11: nine alphanumeric characters (the NSIN)
    - Position 12: single check digit (Luhn algorithm)

    Accepts both upper and lowercase input.

    Args:
        isin_candidate: The string to validate.

    Returns:
        True if the string has the correct ISIN format and checksum,
        False otherwise.
    """

    if not isinstance(isin_candidate, str):
        logging.debug('ISIN must be a string.')
        return False

    isin_candidate = isin_candidate.strip().upper()

    if len(isin_candidate) != 12:
        logging.debug('ISIN must be exactly 12 characters.')
        return False

    # Positions 1-2: two ASCII letters only.
    # isalpha() alone would accept Unicode like umlauts (ä, ö, ü).
    if not (isin_candidate[:2].isascii() and isin_candidate[:2].isalpha()):
        logging.debug('ISIN must start with a two letter country code.')
        return False

    # Positions 3-11: nine ASCII alphanumeric characters only.
    # isalnum() alone would accept Unicode characters.
    if not (isin_candidate[2:11].isascii() and isin_candidate[2:11].isalnum()):
        logging.debug('ISIN positions 3 to 11 must be alphanumeric.')
        return False

    # Position 12: single digit
    if not isin_candidate[11].isdigit():
        logging.debug('Last position of an ISIN must be a digit for checksum.')
        return False

    if not _luhn_check_isin(isin_candidate):
        logging.debug('ISIN Luhn checksum verification failed.')
        return False
    
    return True
