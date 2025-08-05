#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Userprovided: Custom Exceptions

Source: https://github.com/RuedigerVoigt/userprovided
(c) 2019-2021 Rüdiger Voigt:
Released under the Apache License 2.0
"""


class UserprovidedException(Exception):
    """Base exception class for userprovided library.

    All custom exceptions in the userprovided library inherit from this class.
    """
    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        Exception.__init__(self, *args, **kwargs)


class QueryKeyConflict(UserprovidedException):
    """Raised when URL query parameters have duplicate keys with conflicting values.

    This exception is thrown when the same query parameter key appears multiple
    times in a URL with different values, creating an ambiguous situation.
    """


class DeprecatedHashAlgorithm(UserprovidedException):
    """Raised when attempting to use deprecated hash algorithms.

    This exception is thrown when trying to use cryptographically weak or
    deprecated hashing algorithms like MD5 or SHA1 for security reasons.
    """


class ContradictoryParameters(UserprovidedException, ValueError):
    """Raised when mutually exclusive parameters or settings are used together.

    This exception is thrown when function parameters or configuration settings
    contradict each other and cannot be used simultaneously.
    """
