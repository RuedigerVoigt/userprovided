"""
Tests for the package-level setup of userprovided.
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
Released under the Apache License 2.0
"""

# ruff: noqa

import subprocess
import sys

from hypothesis import given, settings, HealthCheck, strategies as st

import userprovided

# Runs in a fresh interpreter: pytest attaches its own handlers to the root
# logger, which would hide any handler the library adds there.
_HOST_APP = """
import logging
import userprovided

userprovided.mail.is_email('not an address')
try:
    userprovided.parameters.validate_dict_keys({'x': 1}, {'a'})
except ValueError:
    pass
logging.basicConfig(level=logging.INFO, format='APP %(message)s')
logging.info('configured')
"""


def test_library_leaves_host_logging_config_alone():
    result = subprocess.run([sys.executable, '-c', _HOST_APP],
                            capture_output=True, text=True, check=True)
    # Only the host's own record, in the host's format. The library's
    # error record must not reach logging's last-resort stderr handler.
    assert result.stderr == 'APP configured\n'


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.text())
def test_records_use_package_logger(caplog, candidate):
    caplog.clear()
    with caplog.at_level('DEBUG', logger='userprovided'):
        userprovided.mail.is_email(candidate)
    assert caplog.records
    assert all(r.name == 'userprovided.mail' for r in caplog.records)
