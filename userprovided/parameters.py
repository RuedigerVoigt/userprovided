#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Check Parameters
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
(c) 2020-2025 Rüdiger Voigt
Released under the Apache License 2.0
"""

import logging
import re
from typing import Optional, Union

from userprovided import err


def convert_to_set(convert_this: Union[list, set, str, tuple]) -> set:
    """Converts various iterable types to a set.

    Takes a string, tuple, list, or existing set and converts it to a set,
    removing any duplicates and creating an unordered collection.

    Args:
        convert_this: The item to convert. Must be a string, tuple, list, or set.

    Returns:
        A set containing the elements from the input.

    Raises:
        TypeError: If convert_this is not a supported type.
    """

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
    """Validates dictionary keys against allowed and required sets.

    Checks if all keys in a dictionary are permitted and whether all
    required keys are present. Useful for parameter validation.

    Args:
        dict_to_check: Dictionary to validate.
        allowed_keys: Set of keys that are permitted in the dictionary.
        necessary_keys: Set of keys that must be present. If None,
            no keys are required. Defaults to None.
        dict_name: Name of the dictionary for error messages.
            Defaults to None.

    Returns:
        True if validation passes.

    Raises:
        ValueError: If unknown keys are found, necessary keys are missing,
            or necessary_keys contains keys not in allowed_keys.
        AttributeError: If dict_to_check is not a dictionary.
    """

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


def keys_neither_none_nor_empty(dict_to_check: dict) -> bool:
    """Validates that all dictionary values are neither None nor empty.

    Checks that no dictionary values are None, empty strings (including
    whitespace-only strings), or empty collections (dict/list/set/tuple).
    Other value types are ignored.

    Args:
        dict_to_check: Dictionary to validate.

    Returns:
        True if all values are non-None and non-empty, False otherwise.

    Raises:
        ValueError: If dict_to_check is not a dictionary or is completely empty.
    """

    if not isinstance(dict_to_check, dict):
        raise ValueError('This is not a dictionary')
    if len(dict_to_check) == 0:
        raise ValueError('This dictionary is empty')

    def error_found() -> None:
        logging.error("Dictionary contains key that is either empty or None!")

    for _, value in dict_to_check.items():
        if value is None:
            error_found()
            return False
        if isinstance(value, str):
            if len(value.strip()) == 0:
                error_found()
                return False
        if isinstance(value, (dict, list, set, tuple)):
            if len(value) == 0:
                error_found()
                return False

    return True


def numeric_in_range(parameter_name: str,
                     given_value: Union[int, float],
                     minimum_value: Union[int, float],
                     maximum_value: Union[int, float],
                     fallback_value: Union[int, float]
                     ) -> Union[int, float]:
    """Validates numeric value within range, returning fallback if outside.

    Checks if a numeric value falls within the specified range. If not,
    returns the fallback value and logs a warning message.

    Args:
        parameter_name: Name of the parameter for logging purposes.
        given_value: The numeric value to check.
        minimum_value: Minimum allowed value (inclusive).
        maximum_value: Maximum allowed value (inclusive).
        fallback_value: Value to return if given_value is outside range.

    Returns:
        The given_value if within range, otherwise fallback_value.

    Raises:
        ValueError: If any parameter is not numeric.
        ContradictoryParameters: If minimum > maximum or fallback_value
            is outside the allowed range.
    """
    if not parameter_name:
        parameter_name = ''

    for param in {given_value, minimum_value, maximum_value, fallback_value}:
        if not isinstance(param, (int, float)):
            raise ValueError('Value must be numeric.')

    if minimum_value > maximum_value:
        raise err.ContradictoryParameters(
            "Minimum must not be larger than maximum value.")

    if fallback_value < minimum_value or fallback_value > maximum_value:
        raise err.ContradictoryParameters(
            "Fallback value outside the allowed range.")

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
    """Validates integer value within range, returning fallback if outside.

    Integer-specific version of numeric_in_range that ensures all parameters
    are integers and performs range validation.

    Args:
        parameter_name: Name of the parameter for logging purposes.
        given_value: The integer value to check.
        minimum_value: Minimum allowed value (inclusive).
        maximum_value: Maximum allowed value (inclusive).
        fallback_value: Value to return if given_value is outside range.

    Returns:
        The given_value if within range, otherwise fallback_value.

    Raises:
        ValueError: If any parameter is not an integer.
        ContradictoryParameters: If minimum > maximum or fallback_value
            is outside the allowed range.
    """
    for param in {given_value, minimum_value, maximum_value, fallback_value}:
        if type(param) != int:  # pylint: disable=unidiomatic-typecheck
            raise ValueError('Value must be an integer.')
    return int(numeric_in_range(parameter_name,
                                given_value,
                                minimum_value,
                                maximum_value,
                                fallback_value))


def is_port(port_number: int) -> bool:
    """Validates if a number is a valid TCP/UDP port.

    Checks whether the provided integer is within the valid port range
    of 0 to 65535 inclusive.

    Args:
        port_number: The port number to validate.

    Returns:
        True if port_number is a valid port, False otherwise.

    Raises:
        ValueError: If port_number is not an integer.
    """

    if not isinstance(port_number, int):
        raise ValueError('Port has to be an integer.')

    if 0 <= port_number <= 65535:
        logging.debug('Port within range')
        return True
    logging.error('Port not within valid range from 0 to 65535')
    return False


def string_in_range(string_to_check: str,
                    minimum_length: int,
                    maximum_length: int,
                    strip_string: bool = True) -> bool:
    """Validates string length within specified limits.

    Optionally strips whitespace from both ends of the string and then
    checks if the resulting length falls within the specified range.

    Args:
        string_to_check: The string to validate.
        minimum_length: Minimum allowed length (inclusive).
        maximum_length: Maximum allowed length (inclusive).
        strip_string: Whether to strip whitespace before checking length.
            Defaults to True.

    Returns:
        True if string length is within range, False otherwise.

    Raises:
        ContradictoryParameters: If minimum_length > maximum_length.
        ValueError: If strip_string is not a boolean.
    """

    if minimum_length > maximum_length:
        raise err.ContradictoryParameters("Minimum must not be larger than maximum value.")
    enforce_boolean(strip_string)

    if strip_string:
        string_to_check = string_to_check.strip()
    if len(string_to_check) < minimum_length:
        logging.info("String length below minimum length.")
        return False
    if len(string_to_check) > maximum_length:
        logging.info("String longer than maximum.")
        return False
    return True


def is_aws_s3_bucket_name(bucket_name: str) -> bool:
    """Validates AWS S3 bucket name compliance.

    Checks if a bucket name follows AWS S3 naming conventions including
    length, character restrictions, format rules, and other constraints.

    Args:
        bucket_name: The bucket name to validate.

    Returns:
        True if the bucket name is valid for AWS S3, False otherwise.

    Note:
        Applies rules from:
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
    # Check for invalid start/end characters
    if bucket_name.startswith('.') or bucket_name.startswith('-'):
        logging.error('AWS bucket name cannot start with dot or hyphen.')
        return False
    if bucket_name.endswith('.') or bucket_name.endswith('-'):
        logging.error('AWS bucket name cannot end with dot or hyphen.')
        return False
    
    # Check for consecutive dots or invalid dot-hyphen patterns
    if '..' in bucket_name or '.-' in bucket_name or '-.' in bucket_name:
        logging.error('AWS bucket name cannot contain consecutive dots or dot-hyphen patterns.')
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
    """Validates that a parameter is a boolean type.

    Ensures the provided parameter is exactly of type bool (not truthy/falsy
    values like 0, 1, '', etc.).

    Args:
        parameter_value: The value to check for boolean type.
        parameter_name: Name of the parameter for error messages.
            Defaults to 'parameter' if None.

    Raises:
        ValueError: If parameter_value is not of type bool.
    """
    if type(parameter_value) != bool:  # pylint: disable=unidiomatic-typecheck
        parameter_name = parameter_name or 'parameter'
        raise ValueError(f"Value of {parameter_name} must be boolean," +
                         "i.e True / False (without quotation marks).")
