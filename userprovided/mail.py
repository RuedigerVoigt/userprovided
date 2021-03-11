#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Checking Email for the userprovided library
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
(c) 2020-2021 Rüdiger Voigt
Released under the Apache License 2.0
"""

# python standard library:
import logging
import re


def is_email(mailaddress: str) -> bool:
    "Very basic check if the email address has a valid format."

    if not mailaddress or mailaddress == '':
        logging.warning('No mail address supplied.')
        return False

    mailaddress = mailaddress.strip()
    if not re.match(r"^[^\s@]+@[^\s@]+\.[a-zA-Z]+", mailaddress):
        logging.error(
            'The supplied mailaddress %s has an unknown format.', mailaddress)
        return False

    logging.debug('%s seems to have a valid format', mailaddress)
    return True
