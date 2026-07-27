#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
userprovided library
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
Copyright (c) 2020-2026 Rüdiger Voigt and contributors

Released under the Apache License 2.0
"""

from importlib.metadata import version

from userprovided import date
from userprovided import err
from userprovided import finance
from userprovided import ip
from userprovided import geo
from userprovided import hashing
from userprovided import mail
from userprovided import parameters
from userprovided import url


NAME = "userprovided"
__version__ = version("userprovided")
__author__ = "Rüdiger Voigt"

__all__ = [
    "date",
    "err",
    "finance",
    "ip",
    "geo",
    "hashing",
    "mail",
    "parameters",
    "url",
]
