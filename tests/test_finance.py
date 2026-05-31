#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for the finance module of userprovided.
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
Released under the Apache License 2.0
"""

# flake8: noqa

import pytest

import userprovided


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
