#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Check Parameters
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
(c) 2020-2021 Rüdiger Voigt
Released under the Apache License 2.0
"""

import logging
import re
from typing import Optional, Union


def convert_to_set(convert_this: Union[list, set, str, tuple]) -> set:
    """ Convert a string, a tuple, or a list into a set
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
    """If you use dictionaries to pass parameters, there are two common errors:
       * misspelled keys
       * necessary keys are missing
       This functions checks whether all keys are in the set of allowed_keys
       and raises ValueError if a unknown key is found.
       It can also check whether all necessary keys are present and
       raises ValueError if not.
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
            msg = ("Contradiction: Not all necessary keys " +
                   "are in the allowed keys set!")
            logging.exception(msg)
            raise ValueError(msg)

    # Get all keys in the dictionary:
    try:
        found_keys = dict_to_check.keys()
    except AttributeError as no_dict:
        raise AttributeError('Expected a dictionary for the dict_to_check ' +
                             'parameter!') from no_dict

    # Check for unknown keys:
    for key in found_keys:
        if key not in allowed_keys:
            msg = f"Unknown key {key} in {dict_name}"
            logging.exception(msg)
            raise ValueError(msg)
    logging.debug('No unknown keys found.')

    # Check if all necessary keys are present:
    if necessary_keys:
        for key in necessary_keys:
            if key not in found_keys:
                msg = f"Necessary key {key} missing in {dict_name}!"
                logging.exception(msg)
                raise ValueError(msg)
        logging.debug('All necessary keys found.')

    return True


def numeric_in_range(parameter_name: str,
                     given_value: Union[int, float],
                     minimum_value: Union[int, float],
                     maximum_value: Union[int, float],
                     fallback_value: Union[int, float]
                     ) -> Union[int, float]:
    """Checks if a numeric value is within a specified range.
       If not this returns the fallback value and logs a warning."""
    if not parameter_name:
        parameter_name = ''

    for param in {given_value, minimum_value, maximum_value, fallback_value}:
        if not isinstance(param, (int, float)):
            raise ValueError('Value must be numeric.')

    if minimum_value > maximum_value:
        raise ValueError("Minimum must not be larger than maximum value.")

    if fallback_value < minimum_value or fallback_value > maximum_value:
        raise ValueError("Fallback value outside the allowed range.")

    if given_value < minimum_value:
        msg = (f"Value of {parameter_name} is below the minimum allowed." +
               f"Falling back to {fallback_value}.")
        logging.warning(msg)
        return fallback_value

    if given_value > maximum_value:
        msg = (f"Value of {parameter_name} is above the maximum allowed." +
               f"Falling back to {fallback_value}.")
        logging.warning(msg)
        return fallback_value

    # passed all checks:
    return given_value


def int_in_range(parameter_name: str,
                 given_value: int,
                 minimum_value: int,
                 maximum_value: int,
                 fallback_value: int) -> int:
    """Special case of numeric_in_range: check if given integer is
       within a specified range of possible values."""
    for param in {given_value, minimum_value, maximum_value, fallback_value}:
        if type(param) != int:  # pylint: disable=unidiomatic-typecheck
            raise ValueError('Value must be an integer.')
    return int(numeric_in_range(parameter_name,
                                given_value,
                                minimum_value,
                                maximum_value,
                                fallback_value))


def is_port(port_number: int) -> bool:
    """Check if the number provided is valid as a TCP/UDP port
       (i.e an integer in the range from 0 to 65535)."""

    if not isinstance(port_number, int):
        raise ValueError('Port has to be an integer.')

    if 0 < port_number < 65536:
        logging.debug('Port within range')
        return True
    logging.error('Port not within valid range from 0 to 65535')
    return False


def string_in_range(string_to_check: str,
                    minimum_length: int,
                    maximum_lenght: int,
                    strip_string: bool = True) -> bool:
    """Strips whitespace from both ends of a string and then checks
       if the length of that string falls in those limits.
       The strip() can be turned off. """

    if minimum_length > maximum_lenght:
        raise ValueError("Minimum must not be larger than maximum value.")
    enforce_boolean(strip_string)

    if strip_string:
        string_to_check = string_to_check.strip()
    if len(string_to_check) < minimum_length:
        logging.info("String length below minimum length.")
        return False
    if len(string_to_check) > maximum_lenght:
        logging.info("String longer than maximum.")
        return False
    return True




def is_aws_s3_bucket_name(bucket_name: str) -> bool:
    """Returns True if bucket name is well-formed for AWS S3 buckets

    Applying the rules set here:
    https://docs.aws.amazon.com/AmazonS3/latest/dev/BucketRestrictions.html
    """

    # Lengthy code which could be written as a single regular expression.
    # However written in this way to provide useful error messages.
    if len(bucket_name) < 3:
        logging.error(
            'Any AWS bucket name has to be at least 3 characters long.')
        return False
    if len(bucket_name) > 63:
        logging.error(
            'The AWS bucket name exceeds the maximum length of 63 characters.')
        return False
    if not re.match(r"^[a-z0-9\-\.]*$", bucket_name):
        logging.error('The AWS bucket name contains invalid characters.')
        return False
    if re.match(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}",
                bucket_name):
        # Check if the bucket name resembles an IPv4 address.
        # No need to check IPv6 as the colon is not an allowed character.
        logging.error('An AWS must not resemble an IP address.')
        return False
    if re.match(r"([a-z0-9][a-z0-9\-]*[a-z0-9]\.)*[a-z0-9][a-z0-9\-]*[a-z0-9]",
                bucket_name):
        # Must start with a lowercase letter or number
        # Bucket names must be a series of one or more labels.
        # Adjacent labels are separated by a single period (.).
        # Each label must start and end with a lowercase letter or a number.
        # => Adopted the answer provided by Zak (zero or more labels
        # followed by a dot) found here:
        # https://stackoverflow.com/questions/50480924
        return True

    logging.error('Invalid AWS bucket name.')
    return False


def enforce_boolean(parameter_value: bool,
                    parameter_name: Optional[str] = None) -> None:
    """Raise a ValueError if the parameter is not of type bool."""
    if type(parameter_value) != bool:  # pylint: disable=unidiomatic-typecheck
        parameter_name = 'parameter' if parameter_name else ''
        raise ValueError(f"Value of {parameter_name} must be boolean," +
                         "i.e True / False (without quotation marks).")
