#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Geographic validation functions of the userprovided library
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
Copyright (c) 2020-2025 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""

import logging
import math
from typing import Union


def is_valid_coordinates(latitude: Union[float, int, str],
                         longitude: Union[float, int, str]) -> bool:
    """Validate if latitude and longitude are within possible Earth ranges.

    Args:
        latitude: Latitude coordinate in decimal degrees.
            Must be convertible to float and within -90 to +90 (inclusive).
        longitude: Longitude coordinate in decimal degrees.
            Must be convertible to float and within -180 to +180 (inclusive).

    Returns:
        True if both coordinates are finite numbers within the valid
        ranges, False otherwise.

    Note:
        Booleans are not accepted, even though they are instances of int.
        Non-finite values (NaN, ±Infinity) are rejected.
        The function only checks mathematical validity. It does not verify
        whether the point is on land, sea, or a specific geographic feature.
    """
    # Explicitly reject booleans (bool is a subclass of int)
    if isinstance(latitude, bool) or isinstance(longitude, bool):
        logging.debug("Boolean passed as coordinate: lat=%r, lng=%r",
                      latitude, longitude)
        return False

    try:
        lat = float(latitude)
        lng = float(longitude)
    except (ValueError, TypeError):
        logging.debug("Invalid coordinate format provided: lat=%r, lng=%r",
                      latitude, longitude)
        return False

    # Reject NaN and Infinity
    if not (math.isfinite(lat) and math.isfinite(lng)):
        logging.debug("Non-finite coordinate(s): lat=%r, lng=%r", lat, lng)
        return False

    if not (-90.0 <= lat <= 90.0):
        logging.debug("Latitude %r is outside valid range (-90 to +90)", lat)
        return False

    if not (-180.0 <= lng <= 180.0):
        logging.debug("Longitude %r is outside valid range (-180 to +180)", lng)
        return False

    logging.debug("Coordinates validated: lat=%r, lng=%r", lat, lng)
    return True
