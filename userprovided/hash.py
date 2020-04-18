#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import logging


def hash_available(hash_method: str,
                   fail_on_deprecated: bool = True) -> bool:
    u"""Checks if the supplied hashing algorithm is available.
        Will raise an exception if not available or deprecated."""

    if hash_method == '' or hash_method is None:
        raise ValueError('No hash method provided')

    # Is the chosen method available and supported?
    hash_method = hash_method.strip()

    if fail_on_deprecated:
        if hash_method in ('md5', 'sha1'):
            raise ValueError('The supplied hash method %s is deprecated!')

    if hash_method in hashlib.algorithms_available:
        logging.debug('Hash method %s is available.', hash_method)
        return True
    else:
        return False
