"""
Tests for the documentation of userprovided.
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
Released under the Apache License 2.0
"""

# ruff: noqa

import importlib
import pathlib
import re

import pytest


_README = pathlib.Path(__file__).resolve().parent.parent / 'README.md'

# Every 'userprovided.<module>.<name>' the README mentions, in prose as well
# as in the examples.
_REFERENCES = sorted(set(re.findall(r'userprovided\.(\w+)\.(\w+)',
                                    _README.read_text(encoding='utf-8'))))


def test_readme_mentions_the_package():
    # Without this the parametrized test below would silently check nothing
    # if the README moved or the pattern stopped matching.
    assert _REFERENCES


@pytest.mark.parametrize("module_name,attribute", _REFERENCES)
def test_readme_documents_existing_names(module_name, attribute):
    # A renamed or removed function is the way the README goes stale most
    # easily, as nothing else reads it.
    module = importlib.import_module(f'userprovided.{module_name}')
    assert hasattr(module, attribute)
