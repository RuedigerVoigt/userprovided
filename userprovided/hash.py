#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hash functionality for the userprovided library
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
(c) 2020-2021 Rüdiger Voigt
Released under the Apache License 2.0
"""

import logging
import pathlib
from typing import Optional, Union
import warnings

from userprovided import hashing


def hash_available(hash_method: str,
                   fail_on_deprecated: bool = True) -> bool:
    """DEPRECATED: use userprovided.hashing.hash_available instead.
       This will fail with userprovied version 1.0.0"""
    msg = 'Deprecated call: method moved to userprovided.hashing'
    logging.warning(msg)
    warnings.warn(msg, DeprecationWarning)
    return hashing.hash_available(hash_method, fail_on_deprecated)


def calculate_file_hash(file_path: Union[pathlib.Path, str],
                        hash_method: str = 'sha256',
                        expected_hash: Optional[str] = None) -> str:
    """DEPRECATED: use userprovided.hashing.calculate_file_hash instead.
       This will fail with userprovied version 1.0.0"""
    msg = 'Deprecated call: method moved to userprovided.hashing'
    logging.warning(msg)
    warnings.warn(msg, DeprecationWarning)
    return hashing.calculate_file_hash(file_path, hash_method, expected_hash)
