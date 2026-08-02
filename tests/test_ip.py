"""
Tests for the ip module of userprovided.
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
Released under the Apache License 2.0
"""

# ruff: noqa

import pytest

import userprovided


def test_parse_ip():
    import ipaddress
    # Standard dotted notation
    assert userprovided.ip._parse_ip('127.0.0.1') == ipaddress.ip_address('127.0.0.1')
    # Decimal integer encoding
    assert userprovided.ip._parse_ip('2130706433') == ipaddress.ip_address('127.0.0.1')
    # Hex encoding
    assert userprovided.ip._parse_ip('0x7f000001') == ipaddress.ip_address('127.0.0.1')
    # Old-style octal encoding
    assert userprovided.ip._parse_ip('017700000001') == ipaddress.ip_address('127.0.0.1')
    # Octal string too large to be a valid IP address — exercises the except branch
    assert userprovided.ip._parse_ip('0' + '7' * 44) is None
    # Plain hostname — not an IP in any encoding
    assert userprovided.ip._parse_ip('example.com') is None


def test_ip_non_string():
    # Every public ip predicate shares the string-validator contract:
    # a non-string argument raises TypeError, not a leaky len() error and
    # not a silent False.
    predicates = (
        userprovided.ip.is_loopback,
        userprovided.ip.is_private,
        userprovided.ip.is_link_local,
        userprovided.ip.is_potential_ssrf_target,
    )
    for predicate in predicates:
        for bad in (None, 123, ['http://127.0.0.1/']):
            with pytest.raises(TypeError):
                predicate(bad)


def test_ip_is_loopback():
    # IPv4 loopback range
    assert userprovided.ip.is_loopback('http://127.0.0.1/') is True
    assert userprovided.ip.is_loopback('http://127.0.0.2/') is True
    assert userprovided.ip.is_loopback('http://127.255.255.255/') is True
    # IPv6 loopback
    assert userprovided.ip.is_loopback('http://[::1]/') is True
    # localhost hostname
    assert userprovided.ip.is_loopback('http://localhost/') is True
    assert userprovided.ip.is_loopback('http://localhost:8080/path') is True
    # Not loopback
    assert userprovided.ip.is_loopback('http://192.168.1.1/') is False
    assert userprovided.ip.is_loopback('http://10.0.0.1/') is False
    assert userprovided.ip.is_loopback('http://example.com/') is False
    assert userprovided.ip.is_loopback('http://8.8.8.8/') is False
    # Malformed
    assert userprovided.ip.is_loopback('not-a-url') is False
    assert userprovided.ip.is_loopback('') is False


def test_ip_is_private():
    # RFC 1918 ranges
    assert userprovided.ip.is_private('http://10.0.0.1/') is True
    assert userprovided.ip.is_private('http://10.255.255.255/') is True
    assert userprovided.ip.is_private('http://172.16.0.1/') is True
    assert userprovided.ip.is_private('http://172.31.255.255/') is True
    assert userprovided.ip.is_private('http://192.168.0.1/') is True
    assert userprovided.ip.is_private('http://192.168.255.255/') is True
    # IPv6 unique-local
    assert userprovided.ip.is_private('http://[fc00::1]/') is True
    assert userprovided.ip.is_private('http://[fd00::1]/') is True
    # Not private
    assert userprovided.ip.is_private('http://8.8.8.8/') is False
    assert userprovided.ip.is_private('http://172.32.0.1/') is False  # outside 172.16/12
    assert userprovided.ip.is_private('http://example.com/') is False
    # Malformed
    assert userprovided.ip.is_private('not-a-url') is False
    assert userprovided.ip.is_private('') is False


def test_ip_is_link_local():
    # IPv4 link-local range (includes cloud metadata endpoint)
    assert userprovided.ip.is_link_local('http://169.254.0.1/') is True
    assert userprovided.ip.is_link_local('http://169.254.169.254/') is True  # AWS/GCP/Azure metadata
    assert userprovided.ip.is_link_local('http://169.254.255.255/') is True
    # IPv6 link-local
    assert userprovided.ip.is_link_local('http://[fe80::1]/') is True
    # .local hostnames (mDNS)
    assert userprovided.ip.is_link_local('http://myprinter.local/') is True
    assert userprovided.ip.is_link_local('http://nas.local:8080/') is True
    # Not link-local
    assert userprovided.ip.is_link_local('http://8.8.8.8/') is False
    assert userprovided.ip.is_link_local('http://192.168.1.1/') is False
    assert userprovided.ip.is_link_local('http://example.com/') is False
    # Malformed
    assert userprovided.ip.is_link_local('not-a-url') is False
    assert userprovided.ip.is_link_local('') is False


def test_ip_is_potential_ssrf_target():
    # Loopback
    assert userprovided.ip.is_potential_ssrf_target('http://127.0.0.1/') is True
    assert userprovided.ip.is_potential_ssrf_target('http://localhost/') is True
    assert userprovided.ip.is_potential_ssrf_target('http://[::1]/') is True
    # Private
    assert userprovided.ip.is_potential_ssrf_target('http://10.0.0.1/') is True
    assert userprovided.ip.is_potential_ssrf_target('http://172.16.0.1/') is True
    assert userprovided.ip.is_potential_ssrf_target('http://192.168.1.1/') is True
    assert userprovided.ip.is_potential_ssrf_target('http://[fc00::1]/') is True
    # Link-local
    assert userprovided.ip.is_potential_ssrf_target('http://169.254.169.254/') is True
    assert userprovided.ip.is_potential_ssrf_target('http://[fe80::1]/') is True
    assert userprovided.ip.is_potential_ssrf_target('http://myhost.local/') is True
    # RFC 6598 carrier-grade NAT (not "private" per ipaddress, but internal)
    assert userprovided.ip.is_potential_ssrf_target('http://100.64.0.1/') is True
    assert userprovided.ip.is_potential_ssrf_target('http://100.127.255.255/') is True
    # Decimal integer encoding of 100.64.0.1 (CGNAT)
    assert userprovided.ip.is_potential_ssrf_target('http://1681915905/') is True
    # Just outside the CGNAT range stays safe
    assert userprovided.ip.is_potential_ssrf_target('http://100.63.255.255/') is False
    assert userprovided.ip.is_potential_ssrf_target('http://100.128.0.0/') is False
    # Safe public addresses
    assert userprovided.ip.is_potential_ssrf_target('https://example.com/') is False
    assert userprovided.ip.is_potential_ssrf_target('http://8.8.8.8/') is False
    assert userprovided.ip.is_potential_ssrf_target('https://www.example.co.uk/') is False
    # No host to check: the guard refuses rather than authorizing a fetch.
    assert userprovided.ip.is_potential_ssrf_target('not-a-url') is True
    assert userprovided.ip.is_potential_ssrf_target('') is True
    # Unclosed IPv6 literal, which urllib cannot parse at all
    assert userprovided.ip.is_potential_ssrf_target('http://[::1') is True
    # Alternate IP encodings that bypass naive ipaddress.ip_address() checks:
    # Decimal integer encoding of 127.0.0.1
    assert userprovided.ip.is_potential_ssrf_target('http://2130706433/') is True
    # Hex encoding of 127.0.0.1
    assert userprovided.ip.is_potential_ssrf_target('http://0x7f000001/') is True
    # Old-style octal encoding of 127.0.0.1
    assert userprovided.ip.is_potential_ssrf_target('http://017700000001/') is True
    # Decimal integer encoding of 192.168.1.1 (private)
    assert userprovided.ip.is_potential_ssrf_target('http://3232235777/') is True
    # Decimal integer encoding of 169.254.169.254 (link-local / cloud metadata)
    assert userprovided.ip.is_potential_ssrf_target('http://2852039166/') is True
    # A large integer that is not a valid IP address
    assert userprovided.ip.is_potential_ssrf_target('http://99999999999999/') is False


def test_ip_long_url_does_not_hide_the_host():
    # An attacker controls the whole URL, so a length limit must not turn
    # a padded URL into "no host found" and therefore "safe".
    padding = 'a' * 4096
    metadata = f'http://169.254.169.254/latest/meta-data/?p={padding}'
    assert userprovided.ip.is_potential_ssrf_target(metadata) is True
    assert userprovided.ip.is_link_local(metadata) is True
    loopback = f'http://127.0.0.1/?x={padding}'
    assert userprovided.ip.is_potential_ssrf_target(loopback) is True
    assert userprovided.ip.is_loopback(loopback) is True
    private = f'http://192.168.1.1/?x={padding}'
    assert userprovided.ip.is_private(private) is True
    # A long URL to a public host stays safe.
    assert userprovided.ip.is_potential_ssrf_target(
        f'https://example.com/?x={padding}') is False
