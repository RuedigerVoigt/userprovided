"""
userprovided library
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
Copyright (c) 2020-2026 Rüdiger Voigt and contributors

Released under the Apache License 2.0
"""

from importlib.metadata import version
import logging

from userprovided import date
from userprovided import err
from userprovided import finance
from userprovided import ip
from userprovided import geo
from userprovided import hashing
from userprovided import mail
from userprovided import parameters
from userprovided import url


# The host application decides where records go; without a handler here,
# they would reach logging's last-resort stderr handler.
logging.getLogger(__name__).addHandler(logging.NullHandler())

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
