#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for the finance module of userprovided.
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
Released under the Apache License 2.0
"""

# ruff: noqa

import string

from hypothesis import given, assume, strategies as st
import pytest

import userprovided


_IBAN_ALPHABET = string.digits + string.ascii_uppercase


def _reference_mod97(value: str) -> int:
    """Independent mod-97 reference (uses Python big ints, not the
    implementation's piecewise routine) for the property tests."""
    numeric = ''.join(str(int(c, 36)) for c in value)  # 0-9 -> self, A-Z -> 10-35
    return int(numeric) % 97


def _reference_check_digits(country: str, bban: str) -> str:
    """Compute the two IBAN check digits independently of the implementation."""
    return f'{98 - _reference_mod97(bban + country + "00"):02d}'


@st.composite
def _valid_ibans(draw):
    """Construct structurally valid IBANs (any 2-letter country, any BBAN
    within the absolute ISO 13616 length bounds, correct check digits)."""
    country = draw(st.text(alphabet=string.ascii_uppercase, min_size=2, max_size=2))
    bban_length = draw(st.integers(min_value=11, max_value=30))  # total 15-34
    bban = draw(st.text(alphabet=_IBAN_ALPHABET,
                        min_size=bban_length, max_size=bban_length))
    return country + _reference_check_digits(country, bban) + bban


@pytest.mark.parametrize("isin,expected", [
    # Valid real ISINs:
    ('DE0007236101', True),   # Siemens
    ('US5949181045', True),   # Microsoft
    ('US0378331005', True),   # Apple
    ('GB00B10RZP78', True),   # Unilever
    # Lowercase input accepted:
    ('de0007236101', True),
    ('us5949181045', True),
    # Mixed case:
    ('De0007236101', True),
    # With leading/trailing whitespace:
    ('  DE0007236101  ', True),
    # Wrong length - too short:
    ('DE000723610', False),
    ('US', False),
    ('', False),
    # Wrong length - too long:
    ('DE00072361011', False),
    ('US59491810451X', False),
    # Invalid country code - digits in positions 0-1:
    ('12345678901', False),
    ('1E0007236101', False),
    ('D10007236101', False),
    # Invalid country code - special characters:
    ('#E0007236101', False),
    ('D@0007236101', False),
    # Invalid country code - umlauts (Unicode but not ASCII):
    ('ÄÖ0007236101', False),
    ('Dü0007236101', False),
    # Invalid characters in NSIN - special characters:
    ('DE000723610!', False),
    ('DE00072#6101', False),
    # Invalid characters in NSIN - umlauts (Unicode but not ASCII):
    ('DE000ä236101', False),
    ('DEöööööööö01', False),
    # Non-digit check digit (letter in position 11):
    ('DE000723610A', False),
    # Failed Luhn checksum (altered last digit):
    ('DE0007236102', False),
    ('US5949181040', False),
])
def test_finance_is_isin(isin, expected):
    assert userprovided.finance.is_isin(isin) is expected


def test_finance_is_isin_non_string():
    assert userprovided.finance.is_isin(123) is False
    assert userprovided.finance.is_isin(None) is False
    assert userprovided.finance.is_isin(['DE0007236101']) is False


def test_finance_luhn_check_isin_invalid_char():
    # Cover the else branch in _luhn_check_isin for unexpected characters
    assert userprovided.finance._luhn_check_isin('DE00072#6101') is False


@pytest.mark.parametrize("iban,expected", [
    # Valid real IBANs from several countries:
    ('DE89370400440532013000', True),
    ('GB82WEST12345698765432', True),
    ('FR1420041010050500013M02606', True),   # contains a letter in the BBAN
    ('NL91ABNA0417164300', True),
    ('BE68539007547034', True),
    ('CH9300762011623852957', True),
    ('NO9386011117947', True),               # shortest (15 chars)
    # Lowercase input accepted:
    ('de89370400440532013000', True),
    # Printed format with spaces:
    ('DE89 3704 0044 0532 0130 00', True),
    # Leading/trailing whitespace:
    ('  DE89370400440532013000  ', True),
    # Wrong checksum (altered last digit):
    ('DE89370400440532013001', False),
    ('GB82WEST12345698765433', False),
    # Check digits replaced with 00 (invalid checksum):
    ('DE00370400440532013000', False),
    # Too short / too long (outside 15-34):
    ('DE89', False),
    ('', False),
    ('DE' + '8' * 40, False),
    # Country code is not two letters:
    ('1234567890123456', False),
    ('D189370400440532013000', False),
    # Country code is Unicode but not ASCII (umlauts):
    ('ÜÄ370400440532013000', False),
    # Check digit positions are not numeric:
    ('DEAB370400440532013000', False),
    # Non-alphanumeric character in the BBAN:
    ('DE8937040044053201300-', False),
])
def test_finance_is_iban(iban, expected):
    assert userprovided.finance.is_iban(iban) is expected


def test_finance_is_iban_non_string():
    assert userprovided.finance.is_iban(123) is False
    assert userprovided.finance.is_iban(None) is False
    assert userprovided.finance.is_iban(['DE89370400440532013000']) is False


@given(_valid_ibans())
def test_finance_is_iban_accepts_constructed_valid(iban):
    # Property: any correctly-constructed IBAN must be accepted.
    assert userprovided.finance.is_iban(iban) is True


@given(_valid_ibans(), st.data())
def test_finance_is_iban_rejects_single_char_mutation(iban, data):
    # Property: changing one BBAN character must break the checksum.
    # Mutate only positions >= 4 so the country code and check digits stay
    # well-formed and validity depends purely on the mod-97 checksum.
    pos = data.draw(st.integers(min_value=4, max_value=len(iban) - 1))
    new_char = data.draw(st.sampled_from(_IBAN_ALPHABET))
    assume(new_char != iban[pos])
    mutated = iban[:pos] + new_char + iban[pos + 1:]
    # Skip the ~1-in-97 case where a single change still satisfies mod-97.
    assume(_reference_mod97(mutated[4:] + mutated[:4]) != 1)
    assert userprovided.finance.is_iban(mutated) is False
