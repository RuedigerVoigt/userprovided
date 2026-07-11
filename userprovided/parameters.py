#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Check Parameters
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
Copyright (c) 2020-2026 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""

import logging
import math
import re

from userprovided import err


# Compiled regex patterns for performance optimization
_AWS_S3_BUCKET_CHARS = re.compile(r"^[a-z0-9\-\.]*$")
_AWS_S3_BUCKET_IPV4 = re.compile(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}")
_AWS_S3_BUCKET_LABELS = re.compile(
    r"^([a-z0-9]([a-z0-9\-]*[a-z0-9])?\.)*"
    r"[a-z0-9]([a-z0-9\-]*[a-z0-9])?$")

# Boolean spellings accepted by parse_boolean (lowercased keys). Mirrors
# configparser.BOOLEAN_STATES, the de-facto standard for config files,
# environment variables, and HTML forms.
_BOOLEAN_STATES = {
    '1': True, 'yes': True, 'true': True, 'on': True,
    '0': False, 'no': False, 'false': False, 'off': False,
}


def convert_to_set(convert_this: list | set | str | tuple) -> set:
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


def separated_string_to_set(
    raw_string: str | None,
    sep: str = ",",
    allow_quotes: bool = True,
    quote_char: str = '"',
) -> set[str] | None:
    r"""Parse a separated string into a set of trimmed, non-empty items.

    Args:
        raw_string: The string to parse. Returns None if None is provided.
        sep: Separator character (single character, default ',').
        allow_quotes: If True, text between quote_char is treated as a
            single field.
        quote_char: Quote character (single character, default '"').

    Returns:
        Set of non-empty trimmed strings, or None if raw_string is None.
        Order not preserved, duplicates collapsed.

    Raises:
        ValueError: If sep or quote_char is not a single character,
            if quote_char equals sep or backslash, or if quotes are
            unclosed.

    Note:
        - Separator: `sep` (single character, default ',').
        - Quotes: when allow_quotes=True, text between `quote_char`
          is a single field.
        - Escaping: backslash (\\) escapes the next character
          (works in/out of quotes), so `\\`, `\sep`, and `\quote_char`
          become literal.
        - Whitespace around fields is trimmed (inside quotes is
          preserved, then trimmed).
        - Empty fields are dropped after trimming.

    Examples:
        >>> separated_string_to_set("a, b, c")
        {'a', 'b', 'c'}
        >>> separated_string_to_set('"hello, world", foo')
        {'hello, world', 'foo'}
        >>> separated_string_to_set("a\\,b,c", sep=",")
        {'a,b', 'c'}
    """
    if raw_string is None:
        return None

    if not isinstance(sep, str) or len(sep) != 1:
        raise ValueError("sep must be a single character.")
    if allow_quotes:
        if not isinstance(quote_char, str) or len(quote_char) != 1:
            raise ValueError("quote_char must be a single character.")
        if quote_char == "\\":
            raise ValueError(
                "quote_char cannot be the backslash escape character.")
        if quote_char == sep:
            raise ValueError("quote_char cannot equal sep.")

    result: set[str] = set()
    buf: list[str] = []
    in_quotes = False
    i = 0
    n = len(raw_string)

    def flush_token() -> None:
        s = "".join(buf).strip()
        if s:  # drop empty after trimming
            result.add(s)
        buf.clear()

    while i < n:
        ch = raw_string[i]

        # Backslash escapes the next character (in/out of quotes)
        if ch == "\\":
            i += 1
            if i < n:
                buf.append(raw_string[i])
                i += 1
            else:
                buf.append("\\")  # trailing backslash: treat as literal
            continue

        # Quote toggling
        if allow_quotes and ch == quote_char:
            in_quotes = not in_quotes
            i += 1
            continue

        # Separator (only when not inside quotes)
        if ch == sep and not in_quotes:
            flush_token()
            i += 1
            continue

        buf.append(ch)
        i += 1

    if in_quotes:
        raise ValueError("Unclosed quoted field.")

    flush_token()
    return result


def validate_dict_keys(dict_to_check: dict,
                       allowed_keys: set,
                       necessary_keys: set | None = None,
                       dict_name: str | None = None) -> bool:
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
            logging.error(msg)
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
            logging.error(msg)
            raise ValueError(msg)
    logging.debug('No unknown keys found.')

    # Check if all necessary keys are present:
    if necessary_keys:
        for key in necessary_keys:
            if key not in found_keys:
                msg = f"Necessary key {key} missing in {dict_name}!"
                logging.error(msg)
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
        logging.debug("Dictionary contains key that is either empty or None!")

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
                     given_value: int | float,
                     minimum_value: int | float,
                     maximum_value: int | float,
                     fallback_value: int | float
                     ) -> int | float:
    """Validates numeric value within range, returning fallback if outside.

    Checks if a numeric value falls within the specified range. If not,
    returns the fallback value and logs a debug message.

    Args:
        parameter_name: Name of the parameter for logging purposes.
        given_value: The numeric value to check.
        minimum_value: Minimum allowed value (inclusive).
        maximum_value: Maximum allowed value (inclusive).
        fallback_value: Value to return if given_value is outside range.

    Returns:
        The given_value if within range, otherwise fallback_value.
        NaN as given_value is treated as out of range and returns
        fallback_value. Infinite bounds (e.g. maximum_value=math.inf
        for "no upper limit") are accepted.

    Raises:
        ValueError: If any parameter is not numeric, or if
            minimum_value, maximum_value, or fallback_value is NaN.
        ContradictoryParameters: If minimum > maximum or fallback_value
            is outside the allowed range.
    """
    if not parameter_name:
        parameter_name = ''

    for param in (given_value, minimum_value, maximum_value, fallback_value):
        if isinstance(param, bool) or not isinstance(param, (int, float)):
            raise ValueError('Value must be numeric.')

    # NaN compares False to everything, so it would defeat the sanity
    # checks below and slip through the range check as "in range".
    for param in (minimum_value, maximum_value, fallback_value):
        if math.isnan(param):
            raise ValueError(
                'Minimum, maximum, and fallback must not be NaN.')

    if minimum_value > maximum_value:
        raise err.ContradictoryParameters(
            "Minimum must not be larger than maximum value.")

    if fallback_value < minimum_value or fallback_value > maximum_value:
        raise err.ContradictoryParameters(
            "Fallback value outside the allowed range.")

    if math.isnan(given_value):
        logging.debug("Value of %r is NaN. Falling back to %r.",
                      parameter_name, fallback_value)
        return fallback_value

    if given_value < minimum_value:
        logging.debug("Value of %r is below the minimum allowed. "
                      "Falling back to %r.",
                      parameter_name, fallback_value)
        return fallback_value

    if given_value > maximum_value:
        logging.debug("Value of %r is above the maximum allowed. "
                      "Falling back to %r.",
                      parameter_name, fallback_value)
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
        if type(param) != int:  # pylint: disable=unidiomatic-typecheck  # noqa: E721
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
    logging.debug('Port not within valid range from 0 to 65535')
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
        TypeError: If string_to_check is not a string.
        ContradictoryParameters: If minimum_length > maximum_length.
        ValueError: If strip_string is not a boolean.
    """

    if not isinstance(string_to_check, str):
        raise TypeError('string_to_check must be a string.')

    if minimum_length > maximum_length:
        raise err.ContradictoryParameters(
            "Minimum must not be larger than maximum value.")
    enforce_boolean(strip_string)

    if strip_string:
        string_to_check = string_to_check.strip()
    if len(string_to_check) < minimum_length:
        logging.debug("String length below minimum length.")
        return False
    if len(string_to_check) > maximum_length:
        logging.debug("String longer than maximum.")
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

    Raises:
        TypeError: If bucket_name is not a string.

    Note:
        Applies rules from:
        https://docs.aws.amazon.com/AmazonS3/latest/dev/BucketRestrictions.html
    """
    if not isinstance(bucket_name, str):
        raise TypeError('Bucket name must be a string.')

    # Lengthy code which could be written as a single regular expression.
    # However written in this way to provide useful error messages.
    if len(bucket_name) < 3:
        logging.debug(
            'Any AWS bucket name has to be at least 3 characters long.')
        return False
    if len(bucket_name) > 63:
        logging.debug(
            'The AWS bucket name exceeds the maximum length of 63 characters.')
        return False
    if not _AWS_S3_BUCKET_CHARS.match(bucket_name):
        logging.debug('The AWS bucket name contains invalid characters.')
        return False
    if _AWS_S3_BUCKET_IPV4.match(bucket_name):
        # Check if the bucket name resembles an IPv4 address.
        # No need to check IPv6 as the colon is not an allowed character.
        logging.debug('An AWS bucket name must not resemble an IP address.')
        return False
    # Check for invalid start/end characters
    if bucket_name.startswith('.') or bucket_name.startswith('-'):
        logging.debug('AWS bucket name cannot start with dot or hyphen.')
        return False
    if bucket_name.endswith('.') or bucket_name.endswith('-'):
        logging.debug('AWS bucket name cannot end with dot or hyphen.')
        return False

    # Check for forbidden prefixes
    forbidden_prefixes = ('xn--', 'sthree-', 'amzn-s3-demo-')
    if bucket_name.startswith(forbidden_prefixes):
        logging.debug('AWS bucket name cannot start with reserved prefixes: %s',
                      ', '.join(forbidden_prefixes))
        return False

    # Check for forbidden suffixes
    forbidden_suffixes = ('-s3alias', '--ol-s3', '.mrap', '--x-s3', '--table-s3')
    if bucket_name.endswith(forbidden_suffixes):
        logging.debug('AWS bucket name cannot end with reserved suffixes: %s',
                      ', '.join(forbidden_suffixes))
        return False

    # Check for consecutive dots or invalid dot-hyphen patterns
    if '..' in bucket_name or '.-' in bucket_name or '-.' in bucket_name:
        logging.debug('AWS bucket name cannot contain consecutive dots '
                      'or dot-hyphen patterns.')
        return False

    # Final validation: Each label (part between dots) must:
    # - Start with a letter or number
    # - End with a letter or number
    # - Can contain hyphens in the middle
    # - Can be a single character
    if _AWS_S3_BUCKET_LABELS.match(bucket_name):
        return True

    logging.debug('Invalid AWS bucket name.')
    return False


def clean_trim(value: str | None,
               empty_as: str | None = None) -> str | None:
    """Strip whitespace and convert empty or whitespace-only strings.

    This is a trivial operation, but it is a repeating input normalization
    pattern in web applications: HTML forms submit empty fields as ``''``
    rather than omitting them. Before storing form data in a database,
    empty strings should be converted to ``None`` so that the column is
    ``NULL`` instead of an empty string. Custom values are possible.
    Non-empty strings are stripped of leading and trailing whitespace.

    Args:
        value: The input value. Typically a string from a web form.
            None is accepted and returned as ``empty_as``.
        empty_as: The value to return when the input is None, empty,
            or whitespace-only. Defaults to None. Set to ``''`` to
            keep empty strings, or to a placeholder like ``'N/A'``.

    Returns:
        ``empty_as`` if value is None, empty, or whitespace-only.
        The stripped string otherwise.

    Raises:
        TypeError: If value is not a string or None.
    """
    if value is None:
        return empty_as
    if not isinstance(value, str):
        raise TypeError('clean_trim expects a string or None.')
    stripped = value.strip()
    if stripped == '':
        return empty_as
    return stripped


def enforce_boolean(parameter_value: bool,
                    parameter_name: str | None = None) -> None:
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
    if type(parameter_value) != bool:  # pylint: disable=unidiomatic-typecheck  # noqa: E721
        parameter_name = parameter_name or 'parameter'
        raise ValueError(f"Value of {parameter_name} must be boolean," +
                         "i.e True / False (without quotation marks).")


def _validation_message(value: object,
                        requirement: str,
                        name: str | None = None,
                        source: str | None = None) -> str:
    """Compose a source-aware validation error message.

    Produces ``Invalid value <value> for <name> <source> - <requirement>.``
    The ``for <name>`` and ``<source>`` clauses are omitted when not given.

    The value is rendered with ``repr()`` (``%r``-style) so that newlines
    and control characters in untrusted input cannot forge or corrupt log
    lines or break a message rendered in a web page.

    Args:
        value: The offending value, shown via repr().
        requirement: What the value should have been (e.g.
            ``'must be an integer >= 0'``).
        name: Optional parameter name.
        source: Optional origin clause (e.g. ``'in config.ini'``).

    Returns:
        The formatted message, ending with a period.
    """
    message = f"Invalid value {value!r}"
    if name:
        message += f" for {name}"
    if source:
        message += f" {source}"
    return f"{message} - {requirement}."


def parse_boolean(value: str | bool,
                  *,
                  name: str | None = None,
                  source: str | None = None) -> bool:
    """Parse a user-supplied boolean value, raising on anything unrecognized.

    Real booleans are returned unchanged. Strings are matched
    case-insensitively (after stripping surrounding whitespace) against the
    spellings delivered by config files, environment variables, and HTML
    forms: ``1`` / ``yes`` / ``true`` / ``on`` become ``True`` and ``0`` /
    ``no`` / ``false`` / ``off`` become ``False`` (mirrors
    ``configparser.BOOLEAN_STATES``).

    Unlike ``enforce_boolean`` (which only checks that a value is already a
    ``bool``), this function converts the string spellings. Unlike a tolerant
    helper, it never falls back to a default — an unrecognized value raises.

    Args:
        value: A ``bool``, or a string spelling of one.
        name: Optional parameter name, used only in the error message.
        source: Optional origin of the value (e.g. ``'in config.ini'`` or
            ``'on the command line (--verbose)'``), used only in the error
            message.

    Returns:
        The parsed boolean.

    Raises:
        ValidationError: If value is a string that is not a recognized
            boolean spelling.
        TypeError: If value is neither a bool nor a string.
    """
    # bool must be checked before str (it is not a str, but be explicit) and
    # before the int-like spellings, so a real bool is returned untouched.
    if isinstance(value, bool):
        return value
    if not isinstance(value, str):
        raise TypeError('parse_boolean expects a bool or a string.')

    parsed = _BOOLEAN_STATES.get(value.strip().lower())
    if parsed is None:
        raise err.ValidationError(
            _validation_message(
                value,
                'must be a boolean (true/false, yes/no, on/off, 1/0)',
                name=name,
                source=source))
    return parsed


def one_of(value: str,
           allowed: set | frozenset | tuple | list | str,
           *,
           name: str | None = None,
           case_sensitive: bool = False,
           source: str | None = None) -> str:
    """Check that a string is one of the allowed options and canonicalize it.

    The value is stripped of surrounding whitespace and matched against
    ``allowed`` — case-insensitively unless ``case_sensitive`` is True. On a
    match the member from ``allowed`` is returned (not the input), so callers
    get the registered spelling in one call: with ``allowed={'HTML'}`` the
    input ``' html '`` returns ``'HTML'``. Anything else raises a
    ``ValidationError`` listing the options.

    Args:
        value: The string to check.
        allowed: The allowed options (set, frozenset, tuple, or list of
            strings; a single string counts as a one-option collection).
        name: Optional parameter name, used only in the error message.
        case_sensitive: If True, the value must match an option exactly.
        source: Optional origin of the value (e.g. ``'in config.ini'``),
            used only in the error message.

    Returns:
        The matching member of ``allowed``.

    Raises:
        ValidationError: If the stripped value is not among the allowed
            options.
        TypeError: If value is not a string, or allowed contains a
            non-string member.
        ValueError: If allowed is empty, or (with case_sensitive=False)
            contains members that differ only in case, which would make
            the match ambiguous.
    """
    if not isinstance(value, str):
        raise TypeError('one_of expects a string value.')
    if isinstance(allowed, frozenset):
        # convert_to_set does not accept frozenset, but membership
        # checks work the same on it.
        allowed_set: set | frozenset = allowed
    else:
        allowed_set = convert_to_set(allowed)
    if not allowed_set:
        raise ValueError('one_of requires at least one allowed option.')
    if not all(isinstance(member, str) for member in allowed_set):
        raise TypeError('one_of expects allowed to contain only strings.')

    stripped = value.strip()
    if case_sensitive:
        if stripped in allowed_set:
            return stripped
    else:
        lookup: dict[str, str] = {}
        for member in allowed_set:
            folded = member.lower()
            if folded in lookup:
                raise ValueError(
                    'one_of: allowed contains members that differ only '
                    f'in case ({lookup[folded]!r} / {member!r}) - the '
                    'case-insensitive match would be ambiguous. Use '
                    'case_sensitive=True or deduplicate allowed.')
            lookup[folded] = member
        match = lookup.get(stripped.lower())
        if match is not None:
            return match

    options = ', '.join(sorted(allowed_set))
    raise err.ValidationError(
        _validation_message(
            value,
            f'must be one of: {options}',
            name=name,
            source=source))
