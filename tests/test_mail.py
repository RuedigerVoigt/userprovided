"""
Tests for the mail module of userprovided.
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
Released under the Apache License 2.0
"""

# ruff: noqa

from hypothesis import given
from hypothesis import settings
from hypothesis import HealthCheck
from hypothesis.strategies import emails
import pytest

import userprovided


@pytest.mark.parametrize("mail_address,truth_value", [
    # valid addresses:
    ('test@example.com', True),
    ('test@example-example.com', True),
    ('test@example.co.uk', True),
    ('  test@example.com  ', True),
    ('test+filter@example.com', True),
    # single character local part:
    ('a@example.com', True),
    ('x@test.org', True),
    # single character domains:
    ('example@x.com', True),
    ('test@a.org', True),
    # valid special characters in local part:
    ('user.name@example.com', True),
    ('user_name@example.com', True),
    ('user-name@example.com', True),
    ('first.last@example.com', True),
    # internationalized domain names (IDN):
    ('test@xn--90ae.com', True),
    ('user@example.xn--node', True),
    ('0@a.xn--90ae', True),
    # invalid addresses - consecutive dots in local part:
    ('test..name@example.com', False),
    ('user...name@example.com', False),
    # invalid addresses - dot at start/end of local part:
    ('.test@example.com', False),
    ('test.@example.com', False),
    ('.test.@example.com', False),
    # invalid addresses - TLD too short (single letter TLDs don't exist):
    ('test@example.c', False),
    ('user@domain.x', False),
    # invalid addresses - domain starts/ends with hyphen:
    ('test@-example.com', False),
    ('test@example-.com', False),
    ('test@exam-ple.com', True),  # hyphen in middle is valid
    # invalid addresses - basic format errors:
    ('@example.com', False),
    ('test@@example.com', False),
    ('test@example.', False),
    ('test@example', False),  # missing TLD
    # multiple @ signs:
    ('user@domain.com@evil.com', False),
    ('test@example@malicious.org', False),
    # extra text after valid email:
    ('test@example.com extra junk', False),
    ('valid@domain.com@another.com', False),
    # missing input:
    ('', False),
    ('   ', False),
    # no @ sign:
    ('testexample.com', False),
    # multiple dots in domain labels:
    ('test@exam..ple.com', False),
    ('test@example..com', False)
])
def test_mail_is_email(mail_address, truth_value):
    assert userprovided.mail.is_email(mail_address) is truth_value


def test_mail_is_email_length_limits():
    # Exactly 254 characters is valid (RFC 5321 maximum)
    local = 'a' * 50
    domain = 'b' * (254 - 50 - 1 - 4)  # subtract local, @, .com
    assert userprovided.mail.is_email(f'{local}@{domain}.com') is True
    # 255 characters is too long
    local = 'a' * 50
    domain = 'b' * (255 - 50 - 1 - 4)
    assert userprovided.mail.is_email(f'{local}@{domain}.com') is False
    # Local part exceeds 64 characters
    assert userprovided.mail.is_email('a' * 65 + '@example.com') is False
    # Local part exactly 64 characters is valid
    assert userprovided.mail.is_email('a' * 64 + '@example.com') is True


def test_mail_is_email_type_validation():
    # Test that None raises TypeError
    with pytest.raises(TypeError, match="Email address must be a string"):
        userprovided.mail.is_email(None)

    # Test that non-string types raise TypeError
    with pytest.raises(TypeError, match="Email address must be a string"):
        userprovided.mail.is_email(123)

    with pytest.raises(TypeError, match="Email address must be a string"):
        userprovided.mail.is_email(['not', 'a', 'string'])


def test_mail_is_email_log_injection(caplog):
    # A rejected address with an embedded newline must not be able to forge
    # a second log line: %r escapes the newline so the log record stays on
    # one line.
    malicious = 'a\n2026-06-14 ERROR forged log line@example.com'
    with caplog.at_level('DEBUG', logger='root'):
        assert userprovided.mail.is_email(malicious) is False
    messages = [rec.getMessage() for rec in caplog.records]
    assert any('has an unknown format' in m for m in messages)
    # No formatted log message may contain a literal newline from the input.
    for m in messages:
        assert '\n' not in m
    # The newline survives in escaped form, proving the value was still logged.
    assert any('\\n' in m for m in messages)


@settings(max_examples=1000,
          suppress_health_check=[HealthCheck.too_slow])
@given(x=emails())
def test_hypothesis_mail_is_email(x):
    assert userprovided.mail.is_email(x) is True
