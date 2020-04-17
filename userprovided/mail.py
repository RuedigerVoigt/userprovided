#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# python standard library:
import logging
import re


def is_email(mailaddress: str) -> bool:
    u"""Very basic check if the email address has a valid format."""

    if mailaddress is None or mailaddress == '':
        logging.warning('No mail address supplied.')
        return False
    else:
        mailaddress = mailaddress.strip()
        if not re.match(r"^[^\s@]+@[^\s@]+\.[a-zA-Z]+", mailaddress):
            logging.error('The supplied mailaddress %s has an unknown ' +
                          'format.', mailaddress)
            return False
        else:
            logging.debug('%s seems to have a valid format', mailaddress)
            return True
