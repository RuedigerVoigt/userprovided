"""
Tests for the geo module of userprovided.
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
Released under the Apache License 2.0
"""

# ruff: noqa

import userprovided


def test_is_valid_coordinates():
    # Valid coordinates - major cities
    assert userprovided.geo.is_valid_coordinates(40.7128, -74.0060) is True  # New York City
    assert userprovided.geo.is_valid_coordinates(51.5074, -0.1278) is True   # London
    assert userprovided.geo.is_valid_coordinates(-33.8688, 151.2093) is True # Sydney
    assert userprovided.geo.is_valid_coordinates(35.6762, 139.6503) is True  # Tokyo

    # Valid coordinates - extremes
    assert userprovided.geo.is_valid_coordinates(90.0, 180.0) is True   # North Pole, Date Line
    assert userprovided.geo.is_valid_coordinates(-90.0, -180.0) is True # South Pole, Date Line
    assert userprovided.geo.is_valid_coordinates(0.0, 0.0) is True      # Equator, Prime Meridian

    # Valid coordinates - string inputs
    assert userprovided.geo.is_valid_coordinates('40.7128', '-74.0060') is True
    assert userprovided.geo.is_valid_coordinates('0', '0') is True

    # Valid coordinates - integer inputs
    assert userprovided.geo.is_valid_coordinates(45, 90) is True
    assert userprovided.geo.is_valid_coordinates(-45, -90) is True

    # Invalid latitude - out of range
    assert userprovided.geo.is_valid_coordinates(91.0, 0.0) is False    # > 90
    assert userprovided.geo.is_valid_coordinates(-91.0, 0.0) is False   # < -90
    assert userprovided.geo.is_valid_coordinates(90.1, 0.0) is False    # Just over 90
    assert userprovided.geo.is_valid_coordinates(-90.1, 0.0) is False   # Just under -90

    # Invalid longitude - out of range
    assert userprovided.geo.is_valid_coordinates(0.0, 181.0) is False   # > 180
    assert userprovided.geo.is_valid_coordinates(0.0, -181.0) is False  # < -180
    assert userprovided.geo.is_valid_coordinates(0.0, 180.1) is False   # Just over 180
    assert userprovided.geo.is_valid_coordinates(0.0, -180.1) is False  # Just under -180

    # Invalid format inputs
    assert userprovided.geo.is_valid_coordinates('invalid', '0') is False
    assert userprovided.geo.is_valid_coordinates('0', 'invalid') is False
    assert userprovided.geo.is_valid_coordinates('abc', 'def') is False
    assert userprovided.geo.is_valid_coordinates(None, 0) is False
    assert userprovided.geo.is_valid_coordinates(0, None) is False
    assert userprovided.geo.is_valid_coordinates('', '') is False

    # Edge case - very precise coordinates
    assert userprovided.geo.is_valid_coordinates(89.9999999, 179.9999999) is True
    assert userprovided.geo.is_valid_coordinates(-89.9999999, -179.9999999) is True

    # Test boolean rejection (bool is subclass of int)
    assert userprovided.geo.is_valid_coordinates(True, False) is False
    assert userprovided.geo.is_valid_coordinates(False, True) is False
    assert userprovided.geo.is_valid_coordinates(True, 90.0) is False
    assert userprovided.geo.is_valid_coordinates(45.0, False) is False

    # Test non-finite values (NaN, Infinity)
    assert userprovided.geo.is_valid_coordinates(float('nan'), 0.0) is False
    assert userprovided.geo.is_valid_coordinates(0.0, float('nan')) is False
    assert userprovided.geo.is_valid_coordinates(float('inf'), 0.0) is False
    assert userprovided.geo.is_valid_coordinates(0.0, float('-inf')) is False
