#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import Optional, Union


def convert_to_set(convert_this: Union[list, set, str, tuple]) -> set:
    u""" Convert a string, a tuple, or a list into a set
    (i.e. no duplicates, unordered)"""

    if isinstance(convert_this, set):
        # functions using this expect a set, so everything
        # else just captures bad input by users
        new_set = convert_this
    elif isinstance(convert_this, str):
        new_set = {convert_this}
    elif isinstance(convert_this, list):
        new_set = set(convert_this)
    elif isinstance(convert_this, tuple):
        new_set = set(convert_this)
    else:
        raise TypeError('The function calling this expects a set.')

    return new_set


def validate_dict_keys(dict_to_check: dict,
                       allowed_keys: set,
                       necessary_keys: Optional[set] = None,
                       dict_name: Optional[str] = None) -> bool:
    u"""If you use dictionaries to pass parameters,
        there are two common errors:
        * misspelled keys
        * necessary keys are missing
        This functions checks whether all keys are in the set
        of allowed_keys and raises ValueError if a unknown key
        is found. It can also check whether all necessary
        keys are present and raises ValueError if not.
        dict_name can be used for a better error message."""

    if not dict_name:
        # fallback to neutral
        dict_name = 'dictionary'

    # In case something other than a set is provided:
    allowed_keys = convert_to_set(allowed_keys)

    if necessary_keys:
        # also make sure it is a set:
        necessary_keys = convert_to_set(necessary_keys)
        # Are all necessary keys in the allowed key list?
        if len(necessary_keys - allowed_keys) != 0:
            msg = (f"Contradiction: Not all necessary keys " +
                   f"are in the allowed keys set!")
            logging.exception(msg)
            raise ValueError(msg)

    # Get all keys in the dictionary:
    try:
        found_keys = dict_to_check.keys()
    except AttributeError:
        raise AttributeError('Expected a dictionary for ' +
                             'the dict_to_check parameter!')

    # Check for unknown keys:
    for key in found_keys:
        if key not in allowed_keys:
            msg = f"Unknown key {key} in {dict_name}"
            logging.exception(msg)
            raise ValueError(msg)
    logging.debug('No unknown keys found.')

    # Check if all necessary keys are present:
    for key in necessary_keys:
        if key not in found_keys:
            msg = f"Necessary key {key} missing in {dict_name}!"
            logging.exception(msg)
            raise ValueError(msg)
    logging.debug('All necessary keys found.')

    return True
