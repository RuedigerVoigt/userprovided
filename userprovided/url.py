#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# python standard library:
import logging
from typing import Union
from urllib.parse import urlparse


def is_url(url: str,
           require_specific_schemes: Union[tuple, None] = None) -> bool:
    u"""Very basic check if the URL fulfills basic conditions
        ("LGTM"). Will not try to connect."""
    parsed = urlparse(url)

    if parsed.scheme == '':
        logging.error('The URL has no scheme (like http or https)')
        return False
    if require_specific_schemes:
        if parsed.scheme not in require_specific_schemes:
            logging.error('Scheme %s not supported.', parsed.scheme)
            return False

    if parsed.netloc == '':
        logging.error('URL is missing or malformed.')
        return False

    return True
