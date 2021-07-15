#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Userprovided: Custom Exceptions

Source: https://github.com/RuedigerVoigt/userprovided
(c) 2019-2021 Rüdiger Voigt:
Released under the Apache License 2.0
"""


class UserprovidedException(Exception):
    "An exception specific to userprovided occured"
    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        Exception.__init__(self, *args, **kwargs)


class QueryKeyConflict(UserprovidedException):
    """Within the query part of the same URL a key is duplicate
       AND the values are not identical."""


class DeprecatedHashAlgorithm(UserprovidedException):
    """If you try to use a deprecated hashing algorithm like MD5 or SHA1,
       this exception is thrown."""


class ContradictoryParameters(UserprovidedException, ValueError):
    """Thrown if the user tries to use settings in a mutually exclusive way."""
