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


def _iban_mod97(rearranged: str) -> int:
    """Compute the ISO 7064 mod-97 value of a rearranged IBAN.

    Each letter is replaced by two digits (A=10, ..., Z=35) and the
    resulting decimal value is reduced modulo 97. The reduction is done
    digit by digit so no very large integer is ever constructed.

    Args:
        rearranged: The IBAN with its first four characters moved to the
            end. Must contain only ASCII letters and digits.

    Returns:
        The remainder modulo 97.
    """
    remainder = 0
    for ch in rearranged:
        # 'A'..'Z' -> '10'..'35'; a digit maps to itself.
        chunk = ch if ch.isdigit() else str(ord(ch) - ord('A') + 10)
        for digit in chunk:
            remainder = (remainder * 10 + (ord(digit) - ord('0'))) % 97
    return remainder


def is_iban(iban_candidate: str) -> bool:
    """Check whether a string has the format of a valid IBAN.

    Validates an International Bank Account Number (ISO 13616) by checking
    its general structure and the ISO 7064 mod-97 check digits.

    This only confirms that the string has the correct *format* and a
    valid checksum. It does NOT verify that the IBAN belongs to a real,
    open bank account, and it does NOT validate the country-specific BBAN
    structure (national bank and branch codes). For either of those you
    need a bank-data provider or per-country rules.

    Limitation:
        This function does not check the country-specific total length,
        because that would require an embedded per-country length table
        that needs ongoing maintenance as the IBAN registry changes. It
        only enforces the absolute ISO 13616 bounds (15 to 34 characters).
        As a consequence it cannot reject a string that has a valid
        checksum but the wrong length for its country, nor does it verify
        that the country code belongs to an IBAN-participating country.

    For a description of the format please refer to:
    * https://en.wikipedia.org/wiki/International_Bank_Account_Number
    * ISO 13616 as the normative source

    An IBAN consists of:
    - Positions 1-2: two letters (ISO 3166-1 alpha-2 country code)
    - Positions 3-4: two check digits
    - Remainder: the BBAN, up to 30 alphanumeric characters.

    Accepts both upper and lowercase input as well as the printed format
    with spaces (e.g. ``DE89 3704 0044 0532 0130 00``).

    Args:
        iban_candidate: The string to validate.

    Returns:
        True if the string has a valid IBAN format and checksum,
        False otherwise.

    Raises:
        TypeError: If iban_candidate is not a string.
    """
    if not isinstance(iban_candidate, str):
        raise TypeError('IBAN must be a string.')

    # Accept the printed format (groups separated by spaces) and any case.
    iban = ''.join(iban_candidate.split()).upper()

    # Absolute ISO 13616 bounds (shortest is NO with 15, spec maximum 34).
    if not 15 <= len(iban) <= 34:
        logging.debug('IBAN length outside the allowed range (15-34).')
        return False

    # Positions 1-2: two ASCII letters (country code).
    # isalpha() alone would accept Unicode like umlauts (ä, ö, ü).
    country = iban[:2]
    if not (country.isascii() and country.isalpha()):
        logging.debug('IBAN must start with a two letter country code.')
        return False

    # Positions 3-4: two check digits.
    if not iban[2:4].isdigit():
        logging.debug('IBAN check digits must be numeric.')
        return False

    # The whole IBAN must be ASCII alphanumeric (guards the BBAN).
    if not (iban.isascii() and iban.isalnum()):
        logging.debug('IBAN must be alphanumeric.')
        return False

    # Move the first four characters to the end, then validate mod-97.
    if _iban_mod97(iban[4:] + iban[:4]) != 1:
        logging.debug('IBAN mod-97 checksum verification failed.')
        return False

    return True


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

    Raises:
        TypeError: If isin_candidate is not a string.
    """

    if not isinstance(isin_candidate, str):
        raise TypeError('ISIN must be a string.')

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
