#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for the parameters module of userprovided.
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
Released under the Apache License 2.0
"""

# ruff: noqa

import math
from unittest.mock import patch

from hypothesis import given, assume, strategies as st
import pytest

import userprovided


@pytest.mark.parametrize("bucket_name,truth_value", [
    ('abc', True),
    # perfectly fine at max length:
    ('iekoht9choofe9eixeeseizoo0iuzos1ibeepae7phee3aeghai7shal9kiepiy', True),
    # too short:
    ('ab', False),
    # too long:
    ('iekoht9choofe9eixeeseizoo0iuzos1ibeepae7phee3aeghaif7shal9kiepiy', False),
    # IPv4:
    ('127.0.0.1', False),
    # invalid characters:
    ('iekoht9choofe9ei_xeeseizo', False),
    ('iekoh#xeeseizo', False),
    ('ab$$c', False),
    ('ABc', False),
    # bucket name must start with lowercase letter or number:
    ('-abc', False),
    # containing dots:
    ('iekoht9choofe.eixeeseizoo0iuzos1ibee.pae7ph', True),
    # edge cases - cannot start with dot or hyphen:
    ('.abc', False),
    ('.test-bucket', False),
    # edge cases - cannot end with dot or hyphen:
    ('abc.', False),
    ('test-bucket.', False),
    ('valid-bucket-', False),
    # edge cases - consecutive dots and invalid patterns:
    ('a..b', False),
    ('test..bucket', False),
    ('a.-b', False),
    ('-a.b', False),  # label starts with hyphen
    ('a-.b', False),  # label ends with hyphen
    # single character labels are valid per AWS rules:
    ('a.b', True),
    ('x.y.z', True),
    ('1.a', True),
    ('a.1', True),
    ('a.test', True),
    # forbidden prefixes:
    ('xn--bucket', False),
    ('xn--test-example', False),
    ('sthree-bucket', False),
    ('sthree-example-name', False),
    ('amzn-s3-demo-bucket', False),
    ('amzn-s3-demo-test', False),
    # valid names that contain but don't start with forbidden prefixes:
    ('my-xn--bucket', True),
    ('test-sthree-bucket', True),
    ('my-amzn-s3-demo-bucket', True),
    # forbidden suffixes:
    ('bucket-s3alias', False),
    ('test-bucket-s3alias', False),
    ('bucket--ol-s3', False),
    ('test--ol-s3', False),
    ('bucket.mrap', False),
    ('test.mrap', False),
    ('bucket--x-s3', False),
    ('test--x-s3', False),
    ('bucket--table-s3', False),
    ('test--table-s3', False),
    # valid names that contain but don't end with forbidden suffixes:
    ('s3alias-bucket', True),
    ('ol-s3-test', True),
    ('mrap-bucket', True),
    ('x-s3-test', True),
    ('table-s3-bucket', True)
])
def test_cloud_is_aws_s3_bucket_name(bucket_name, truth_value):
    assert userprovided.parameters.is_aws_s3_bucket_name(bucket_name) is truth_value


def test_is_aws_s3_bucket_name_non_string():
    # Non-string input is a caller error and raises TypeError.
    with pytest.raises(TypeError):
        userprovided.parameters.is_aws_s3_bucket_name(None)
    with pytest.raises(TypeError):
        userprovided.parameters.is_aws_s3_bucket_name(123)
    with pytest.raises(TypeError):
        userprovided.parameters.is_aws_s3_bucket_name(['my-bucket'])


def test_parameters_is_port():
    assert userprovided.parameters.is_port(443) is True
    assert userprovided.parameters.is_port(65536) is False
    assert userprovided.parameters.is_port(-1) is False
    with pytest.raises(ValueError):
        userprovided.parameters.is_port('foo')
    with pytest.raises(ValueError):
        userprovided.parameters.is_port(None)


@pytest.mark.parametrize("input,expected", [
    # single string with multiple characters
    # (wrong would be turning each character into an element)
    ('abc', {'abc'}),
    # list with duplicates to set:
    (['a', 'a', 'b', 'c'], {'a', 'b', 'c'}),
    # tuple with duplicates:
    (('a', 'a', 'b', 'c'), {'a', 'b', 'c'}),
    # a set should return unchanged:
    ({'a', 'b', 'c'}, {'a', 'b', 'c'})
])
def test_convert_to_set(input, expected):
    assert userprovided.parameters.convert_to_set(input) == expected


def test_convert_to_set_exceptions():
    # unsupported data type integer
    with pytest.raises(TypeError):
        userprovided.parameters.convert_to_set(3)


def test_separated_string_to_set_basic():
    # None input returns None
    assert userprovided.parameters.separated_string_to_set(None) is None

    # Empty string returns empty set
    assert userprovided.parameters.separated_string_to_set('') == set()

    # Simple comma-separated values
    assert userprovided.parameters.separated_string_to_set('a,b,c') == \
        {'a', 'b', 'c'}

    # Values with whitespace (should be trimmed)
    assert userprovided.parameters.separated_string_to_set('a, b , c') == \
        {'a', 'b', 'c'}

    # Duplicates should be collapsed (set behavior)
    assert userprovided.parameters.separated_string_to_set('a,b,a,c,b') == \
        {'a', 'b', 'c'}

    # Empty fields should be dropped
    assert userprovided.parameters.separated_string_to_set('a,,b,  ,c') == \
        {'a', 'b', 'c'}
    assert userprovided.parameters.separated_string_to_set(',,a,,') == {'a'}


def test_separated_string_to_set_quotes():
    # Quoted field with separator inside
    assert userprovided.parameters.separated_string_to_set(
        '"hello, world",foo') == {'hello, world', 'foo'}

    # Multiple quoted fields
    assert userprovided.parameters.separated_string_to_set(
        '"a,b","c,d"') == {'a,b', 'c,d'}

    # Whitespace inside quotes is preserved, then trimmed
    assert userprovided.parameters.separated_string_to_set(
        '"  spaces  "') == {'spaces'}

    # Empty quoted field is dropped after trimming
    assert userprovided.parameters.separated_string_to_set(
        '"",a') == {'a'}
    assert userprovided.parameters.separated_string_to_set(
        '"   ",a') == {'a'}

    # Quotes disabled
    assert userprovided.parameters.separated_string_to_set(
        '"a,b",c', allow_quotes=False) == {'"a', 'b"', 'c'}


def test_separated_string_to_set_escaping():
    # Escaped separator
    result = userprovided.parameters.separated_string_to_set('a\\,b,c')
    assert result == {'a,b', 'c'}

    # Escaped quote
    result = userprovided.parameters.separated_string_to_set('a\\"b,c')
    assert result == {'a"b', 'c'}

    # Escaped backslash
    result = userprovided.parameters.separated_string_to_set('a\\\\,b')
    assert result == {'a\\', 'b'}

    # Trailing backslash (treated as literal)
    result = userprovided.parameters.separated_string_to_set('a\\')
    assert result == {'a\\'}

    # Escaping works inside quotes
    result = userprovided.parameters.separated_string_to_set(
        '"a\\,b",c')
    assert result == {'a,b', 'c'}


def test_separated_string_to_set_custom_separator():
    # Pipe separator
    assert userprovided.parameters.separated_string_to_set(
        'a|b|c', sep='|') == {'a', 'b', 'c'}

    # Semicolon separator
    assert userprovided.parameters.separated_string_to_set(
        'a;b;c', sep=';') == {'a', 'b', 'c'}

    # Tab separator
    assert userprovided.parameters.separated_string_to_set(
        'a\tb\tc', sep='\t') == {'a', 'b', 'c'}


def test_separated_string_to_set_custom_quote():
    # Single quote as quote char
    assert userprovided.parameters.separated_string_to_set(
        "'a,b',c", quote_char="'") == {'a,b', 'c'}

    # Pipe as quote char (unusual but valid)
    assert userprovided.parameters.separated_string_to_set(
        '|a,b|,c', sep=',', quote_char='|') == {'a,b', 'c'}


def test_separated_string_to_set_errors():
    # Multi-character separator
    with pytest.raises(ValueError, match="sep must be a single character"):
        userprovided.parameters.separated_string_to_set('a,b', sep=',,')

    # Empty separator
    with pytest.raises(ValueError, match="sep must be a single character"):
        userprovided.parameters.separated_string_to_set('a,b', sep='')

    # Multi-character quote
    with pytest.raises(ValueError,
                       match="quote_char must be a single character"):
        userprovided.parameters.separated_string_to_set('a,b',
                                                        quote_char='""')

    # Empty quote char
    with pytest.raises(ValueError,
                       match="quote_char must be a single character"):
        userprovided.parameters.separated_string_to_set('a,b', quote_char='')

    # Quote char equals backslash
    with pytest.raises(ValueError,
                       match="quote_char cannot be the backslash"):
        userprovided.parameters.separated_string_to_set(
            'a,b', quote_char='\\')

    # Quote char equals separator
    with pytest.raises(ValueError, match="quote_char cannot equal sep"):
        userprovided.parameters.separated_string_to_set(
            'a,b', sep=',', quote_char=',')

    # Unclosed quotes
    with pytest.raises(ValueError, match="Unclosed quoted field"):
        userprovided.parameters.separated_string_to_set('"a,b')

    with pytest.raises(ValueError, match="Unclosed quoted field"):
        userprovided.parameters.separated_string_to_set('a,"b,c')


def test_separated_string_to_set_edge_cases():
    # Only separators
    assert userprovided.parameters.separated_string_to_set(',,,') == set()

    # Only whitespace
    assert userprovided.parameters.separated_string_to_set('   ') == set()

    # Single value
    assert userprovided.parameters.separated_string_to_set('single') == \
        {'single'}

    # Single quoted value
    assert userprovided.parameters.separated_string_to_set(
        '"single"') == {'single'}

    # Complex combination
    assert userprovided.parameters.separated_string_to_set(
        ' "a,b" , c\\,d , , e ') == {'a,b', 'c,d', 'e'}


@pytest.mark.parametrize("input_str,expected", [
    ('a,b,c', {'a', 'b', 'c'}),
    ('  a  ,  b  ,  c  ', {'a', 'b', 'c'}),
    ('"a,b",c', {'a,b', 'c'}),
    ('a\\,b,c', {'a,b', 'c'}),
    ('a,a,b,c', {'a', 'b', 'c'}),  # duplicates
    ('', set()),
    ('a', {'a'}),
    ('a,', {'a'}),
    (',a', {'a'}),
])
def test_separated_string_to_set_parametrized(input_str, expected):
    assert userprovided.parameters.separated_string_to_set(
        input_str) == expected


def test_validate_dict_keys():
    # not a dictionary
    with pytest.raises(AttributeError):
        userprovided.parameters.validate_dict_keys(
            {'a', 'b', 'c'},
            {'a', 'b'})
    # unknown key in dictionary, but no necessary keys
    with pytest.raises(ValueError):
        userprovided.parameters.validate_dict_keys(
            {'a': 1, 'b': 2, 'c': 3},
            {'a', 'b'})
    # missing a necessary key in dictionary to test
    with pytest.raises(ValueError):
        userprovided.parameters.validate_dict_keys(
            {'a': 1, 'b': 2},
            {'a', 'b', 'c'},
            {'b', 'c'})
    # necessary_keys contains a key missing in allowed_keys
    with pytest.raises(ValueError):
        userprovided.parameters.validate_dict_keys(
            {'a': 1, 'b': 2, 'c': 3},
            {'a', 'b', 'c'},
            {'b', 'c', 'd'})
    # Valid:
    assert userprovided.parameters.validate_dict_keys(
            {'a': 1, 'b': 2},
            {'a', 'b', 'c'},
            {'a', 'b'},
            'name') is True
    # Valid with no necessary_keys (default None):
    assert userprovided.parameters.validate_dict_keys(
            {'a': 1},
            {'a', 'b'}) is True


@pytest.mark.parametrize("dict_to_check,truth_value", [
    # valid input:
    ({'a': 'foo', 'b': 'example', 'c': 'foo'}, True),
    ({'a': 'foo', 'b': 'example', 'c': {'foo': 'foo'}}, True),
    ({'a': 'foo', 'b': 'example', 'c': [1, 2, 3]}, True),
    ({'a': 'foo', 'b': 'example', 'c': (1, 2, 3)}, True),
    ({'a': 'foo', 'b': 'example', 'c': {1, 2, 3}}, True),
    ({'a': 1, 'b': 2, 'c': 3}, True),
    # Some key is None:
    ({'a': 1, 'b': 2, 'c': None}, False),
    # Keys with empty value:
    ({'a': 1, 'b': 2, 'c': ''}, False),
    ({'a': 1, 'b': 2, 'c': '      '}, False),
    ({'a': 1, 'b': 2, 'c': '\t'}, False),
    ({'a': 1, 'b': 2, 'c': str()}, False),
    ({'a': 1, 'b': 2, 'c': list()}, False),
    ({'a': 1, 'b': 2, 'c': tuple()}, False),
    ({'a': 1, 'b': 2, 'c': dict()}, False)
    ])
def test_keys_neither_none_nor_empty(
    dict_to_check: dict, truth_value: bool):
    assert userprovided.parameters.keys_neither_none_nor_empty(dict_to_check) is truth_value

def test_keys_neither_none_nor_empty_false_input():
    # not a dictionary
    with pytest.raises(ValueError):
        userprovided.parameters.keys_neither_none_nor_empty('foo')
    # empty dictionary
    with pytest.raises(ValueError):
        userprovided.parameters.keys_neither_none_nor_empty(dict())

def test_numeric_in_range():
    # Minimum value larger than maximum value
    with pytest.raises(userprovided.err.ContradictoryParameters):
        userprovided.parameters.numeric_in_range(
            'example',
            101,
            100,
            1.0,
            50)

    # Fallback value outside the allowed range
    with pytest.raises(userprovided.err.ContradictoryParameters):
        userprovided.parameters.numeric_in_range(
            'example',
            101,
            100,
            200,
            5000  # fallback larger than maximum
            )
    with pytest.raises(userprovided.err.ContradictoryParameters):
        userprovided.parameters.numeric_in_range(
            'example',
            101,
            100,
            200,
            0  # fallback smaller than minimum
            )

    # One of the values not numeric
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range(
            'example',
            'some string',
            100,
            1.0,
            0)
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range(
            'example',
            101,
            'some string',
            1.0,
            0)
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range(
            'example',
            101,
            100,
            'some string',
            0)
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range(
            'example',
            101,
            100,
            1.0,
            'some string')
    # no paramter name
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range(
            None,
            101,
            100,
            1.0,
            'some string')

    # bool must be rejected even though bool is a subclass of int
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range('example', True, 0, 10, 5)
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range('example', False, 0, 10, 5)
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range('example', 5, True, 10, 5)
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range('example', 5, False, 10, 5)
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range('example', 5, 0, True, 5)
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range('example', 5, 0, False, 5)
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range('example', 5, 0, 10, True)
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range('example', 5, 0, 10, False)

    # given value within range
    assert userprovided.parameters.numeric_in_range('example', 10.0, 1, 100, 50) == 10.0

    # given value too large => fallback
    assert userprovided.parameters.numeric_in_range('example', 101, 1, 100, 50) == 50

    # given value to small => fallback
    assert userprovided.parameters.numeric_in_range('example', 3, 10, 100, 50) == 50


def test_numeric_in_range_nan_given_value():
    # NaN compares False to any bound, so it used to slip through the
    # range check and was returned as "in range". It must be treated
    # like any other out-of-range user input: return the fallback.
    assert userprovided.parameters.numeric_in_range(
        'example', math.nan, 0.0, 10.0, 1.0) == 1.0


@pytest.mark.parametrize("minimum,maximum,fallback", [
    (math.nan, 10.0, 5.0),
    (0.0, math.nan, 5.0),
    (0.0, 10.0, math.nan),
])
def test_numeric_in_range_nan_bounds_raise(minimum, maximum, fallback):
    # NaN as a bound or fallback defeats the sanity checks
    # (every comparison is False) => caller error
    with pytest.raises(ValueError):
        userprovided.parameters.numeric_in_range(
            'example', 5.0, minimum, maximum, fallback)


def test_numeric_in_range_infinite_bound_accepted():
    # an infinite bound is legitimate ("no upper limit") - only NaN is rejected
    assert userprovided.parameters.numeric_in_range(
        'example', 5.0, 0.0, math.inf, 1.0) == 5.0
    # inf as given value falls out of a finite range => fallback
    assert userprovided.parameters.numeric_in_range(
        'example', math.inf, 0.0, 10.0, 1.0) == 1.0


@given(
    given_value=st.floats(allow_nan=False, allow_infinity=False),
    minimum=st.floats(allow_nan=False, allow_infinity=False),
    maximum=st.floats(allow_nan=False, allow_infinity=False),
    fallback=st.floats(allow_nan=False, allow_infinity=False))
def test_numeric_in_range_never_returns_nan(
        given_value, minimum, maximum, fallback):
    assume(minimum <= fallback <= maximum)
    result = userprovided.parameters.numeric_in_range(
        'example', given_value, minimum, maximum, fallback)
    assert result == given_value or result == fallback
    assert not math.isnan(result)


def test_int_in_range():
    # parmeter is not integer
    with pytest.raises(ValueError):
        userprovided.parameters.int_in_range(
            'example',
            10,
            1,
            100.0,
            50)
    # parameter is string
    with pytest.raises(ValueError):
        userprovided.parameters.int_in_range(
            'example',
            10,
            1,
            'foo',
            50)
    # given value within range
    assert userprovided.parameters.int_in_range('foo', 10, 1, 100, 50) == 10
    # given value to small => fallback
    assert userprovided.parameters.int_in_range('foo', 3, 10, 100, 50) == 50
    # a float NaN is not an int => rejected by the type check
    with pytest.raises(ValueError):
        userprovided.parameters.int_in_range('foo', math.nan, 1, 100, 50)


def test_string_in_range():
    # string within range
    assert userprovided.parameters.string_in_range('foo', 1, 5) is True
    # default is to apply strip() to the string
    assert userprovided.parameters.string_in_range('     foo      ', 3, 3) is True
    # switch off strip()
    assert userprovided.parameters.string_in_range('     foo      ', 3, 3, False) is False
    # string too long
    assert userprovided.parameters.string_in_range('     foo      ', 1, 2) is False
    # string to short
    assert userprovided.parameters.string_in_range('     foo      ', 5, 10) is False
    # parameters contradict each other
    with pytest.raises(userprovided.err.ContradictoryParameters):
        userprovided.parameters.string_in_range('example', 10, 5)
    # not a string - test TypeError
    with pytest.raises(TypeError):
        userprovided.parameters.string_in_range(123, 1, 5)
    with pytest.raises(TypeError):
        userprovided.parameters.string_in_range(None, 1, 5)


@pytest.mark.parametrize("value,expected", [
    # None passthrough:
    (None, None),
    # Empty string:
    ('', None),
    # Whitespace-only strings:
    ('   ', None),
    ('\t', None),
    ('\n', None),
    ('  \t\n  ', None),
    # Non-empty strings return stripped:
    ('hello', 'hello'),
    ('  hello  ', 'hello'),
    ('\thello\n', 'hello'),
    ('  some value  ', 'some value'),
    # Single character:
    ('a', 'a'),
    (' a ', 'a'),
])
def test_clean_trim(value, expected):
    assert userprovided.parameters.clean_trim(value) == expected


def test_clean_trim_empty_as():
    # empty_as='' returns empty string instead of None
    assert userprovided.parameters.clean_trim('', empty_as='') == ''
    assert userprovided.parameters.clean_trim('   ', empty_as='') == ''
    assert userprovided.parameters.clean_trim(None, empty_as='') == ''
    # empty_as with custom placeholder
    assert userprovided.parameters.clean_trim('', empty_as='N/A') == 'N/A'
    assert userprovided.parameters.clean_trim('   ', empty_as='N/A') == 'N/A'
    assert userprovided.parameters.clean_trim(None, empty_as='N/A') == 'N/A'
    # Non-empty strings still return stripped, regardless of empty_as
    assert userprovided.parameters.clean_trim('  hello  ', empty_as='N/A') == 'hello'


def test_clean_trim_type_error():
    with pytest.raises(TypeError):
        userprovided.parameters.clean_trim(123)
    with pytest.raises(TypeError):
        userprovided.parameters.clean_trim([])
    with pytest.raises(TypeError):
        userprovided.parameters.clean_trim(False)


def test_enforce_boolean():
    # string instead of boolean
    with pytest.raises(ValueError):
        userprovided.parameters.enforce_boolean('True')
    # numeric instead of boolean
    with pytest.raises(ValueError):
        userprovided.parameters.enforce_boolean(1)
    # set parameter_name
    with pytest.raises(ValueError):
        userprovided.parameters.enforce_boolean(1, 'example')
    # valid calls:
    userprovided.parameters.enforce_boolean(True)
    userprovided.parameters.enforce_boolean(False)


@pytest.mark.parametrize("value,expected", [
    # real booleans pass through unchanged:
    (True, True),
    (False, False),
    # truthy spellings:
    ('1', True), ('yes', True), ('true', True), ('on', True),
    # falsy spellings:
    ('0', False), ('no', False), ('false', False), ('off', False),
    # case-insensitive and whitespace-trimmed:
    ('YES', True), ('Off', False), ('  on  ', True), ('\tTrue\n', True),
])
def test_parse_boolean_valid(value, expected):
    assert userprovided.parameters.parse_boolean(value) is expected


def test_parse_boolean_invalid_string():
    # An unrecognized spelling raises ValidationError ...
    with pytest.raises(userprovided.err.ValidationError):
        userprovided.parameters.parse_boolean('maybe')
    # ... which is also a ValueError (backward-compatible handling) ...
    with pytest.raises(ValueError):
        userprovided.parameters.parse_boolean('maybe')
    # ... and a UserprovidedException.
    with pytest.raises(userprovided.err.UserprovidedException):
        userprovided.parameters.parse_boolean('')


def test_parse_boolean_non_string():
    # Neither bool nor string is a caller error -> TypeError, not ValidationError.
    for bad in (None, 1, 0, 1.0, ['yes']):
        with pytest.raises(TypeError):
            userprovided.parameters.parse_boolean(bad)


def test_parse_boolean_error_message():
    # The message names the value, the parameter, the source, and the rule.
    with pytest.raises(userprovided.err.ValidationError) as excinfo:
        userprovided.parameters.parse_boolean(
            'nope', name='verbose', source='in config.ini')
    msg = str(excinfo.value)
    assert "'nope'" in msg
    assert 'for verbose' in msg
    assert 'in config.ini' in msg
    assert 'true/false, yes/no, on/off, 1/0' in msg
    # Without name/source the extra clauses are absent.
    with pytest.raises(userprovided.err.ValidationError) as excinfo2:
        userprovided.parameters.parse_boolean('nope')
    bare = str(excinfo2.value)
    assert ' for ' not in bare
    assert bare.startswith("Invalid value 'nope' -")


def test_parse_boolean_message_no_log_injection():
    # A value with an embedded newline must not be able to forge a second
    # log line: repr() escapes it, so the message stays on one line.
    with pytest.raises(userprovided.err.ValidationError) as excinfo:
        userprovided.parameters.parse_boolean('a\nFAKE LOG LINE')
    msg = str(excinfo.value)
    assert '\n' not in msg
    assert '\\n' in msg


@pytest.mark.parametrize("value,allowed,expected", [
    # case-insensitive by default; the member from allowed is returned,
    # so the caller gets the registered spelling, not the input:
    ('html', {'HTML', 'markdown'}, 'HTML'),
    (' html ', ['HTML'], 'HTML'),
    ('Markdown', ('markdown', 'tex'), 'markdown'),
    # a single string is a one-option collection (via convert_to_set):
    ('TEX', 'tex', 'tex'),
    # frozenset works too:
    ('a', frozenset({'a', 'b'}), 'a'),
])
def test_one_of_valid(value, allowed, expected):
    assert userprovided.parameters.one_of(value, allowed) == expected


def test_one_of_case_sensitive():
    # An exact match is required (whitespace is still stripped):
    assert userprovided.parameters.one_of(
        ' HTML ', {'HTML', 'html'}, case_sensitive=True) == 'HTML'
    with pytest.raises(userprovided.err.ValidationError):
        userprovided.parameters.one_of(
            'Html', {'HTML', 'html'}, case_sensitive=True)


def test_one_of_invalid_value():
    # An unknown option raises ValidationError ...
    with pytest.raises(userprovided.err.ValidationError):
        userprovided.parameters.one_of('yaml', {'html', 'markdown'})
    # ... which is also a ValueError (backward-compatible handling).
    with pytest.raises(ValueError):
        userprovided.parameters.one_of('yaml', {'html', 'markdown'})


def test_one_of_non_string_value():
    # A non-string value is a caller error -> TypeError, not ValidationError.
    for bad in (None, 1, 1.0, ['html'], {'html'}):
        with pytest.raises(TypeError):
            userprovided.parameters.one_of(bad, {'html'})


def test_one_of_caller_errors():
    # An empty allowed collection is a caller error, not a validation failure:
    with pytest.raises(ValueError):
        userprovided.parameters.one_of('html', set())
    # Non-string members cannot be matched:
    with pytest.raises(TypeError):
        userprovided.parameters.one_of('1', {1, 2})
    # Members differing only in case make the default (case-insensitive)
    # match ambiguous:
    with pytest.raises(ValueError):
        userprovided.parameters.one_of('html', {'HTML', 'html'})


def test_one_of_error_message():
    # The message names the value, the parameter, the source, and the
    # sorted options (deterministic even for set input).
    with pytest.raises(userprovided.err.ValidationError) as excinfo:
        userprovided.parameters.one_of(
            'yaml', {'markdown', 'html', 'tex'},
            name='output_format', source='in config.ini')
    msg = str(excinfo.value)
    assert "'yaml'" in msg
    assert 'for output_format' in msg
    assert 'in config.ini' in msg
    assert 'must be one of: html, markdown, tex' in msg


def test_aws_s3_bucket_label_regex_fallback():
    """Cover the final regex fallback (parameters.py lines 503-504).

    The preceding checks already reject all inputs that would fail the
    label regex, making this path effectively unreachable under normal
    conditions.  We patch the regex to force the fallback path."""
    with patch('userprovided.parameters._AWS_S3_BUCKET_LABELS') as mock_re:
        mock_re.match.return_value = None
        assert userprovided.parameters.is_aws_s3_bucket_name('valid') is False
