#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
IP address related functions of the userprovided library
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
Copyright (c) 2020-2026 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""

# python standard library:
import ipaddress
import logging

from userprovided.url import _host_from_url


def is_loopback(url: str) -> bool:
    """Check whether the host in a URL resolves to a loopback address.

    Returns True for IP addresses in the loopback range (127.0.0.0/8 for
    IPv4, ::1 for IPv6) and for the hostname ``localhost``.

    Args:
        url: The URL whose host to check.

    Returns:
        True if the host is a loopback address or ``localhost``,
        False otherwise (including malformed URLs).
    """
    host = _host_from_url(url)
    if host is None:
        return False
    if host == 'localhost':
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def is_private(url: str) -> bool:
    """Check whether the host in a URL is a private IP address.

    Uses Python's ``ipaddress.ip_address.is_private``, which covers the
    RFC 1918 ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16) and the
    IPv6 unique-local range (fc00::/7).

    Note:
        The exact set of addresses considered private depends on the Python
        version. See the ``ipaddress`` module documentation for details.

    Args:
        url: The URL whose host to check.

    Returns:
        True if the host is a private IP address, False otherwise
        (including malformed URLs and hostnames that are not IP addresses).
    """
    host = _host_from_url(url)
    if host is None:
        return False
    try:
        return ipaddress.ip_address(host).is_private
    except ValueError:
        return False


def is_link_local(url: str) -> bool:
    """Check whether the host in a URL is a link-local address.

    Returns True for IPv4 link-local addresses (169.254.0.0/16, which
    includes the cloud metadata endpoint 169.254.169.254), IPv6 link-local
    addresses (fe80::/10), and hostnames ending with ``.local`` (mDNS).

    Args:
        url: The URL whose host to check.

    Returns:
        True if the host is link-local or a ``.local`` hostname, False
        otherwise (including malformed URLs).
    """
    host = _host_from_url(url)
    if host is None:
        return False
    if host.endswith('.local'):
        return True
    try:
        return ipaddress.ip_address(host).is_link_local
    except ValueError:
        return False


def is_potential_ssrf_target(url: str) -> bool:
    """Check whether a URL is a potential SSRF (Server-Side Request Forgery) target.

    Returns True if the URL's host is a loopback address, a private IP,
    or a link-local address. This covers the most common internal targets
    an attacker would attempt to reach via SSRF:

    * Loopback: 127.0.0.0/8, ::1, ``localhost``
    * Private (RFC 1918): 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
    * Link-local: 169.254.0.0/16 (incl. cloud metadata at 169.254.169.254),
      fe80::/10, ``.local`` hostnames

    This function does **not** perform DNS resolution. Hostnames that are
    not IP addresses (other than ``localhost`` and ``.local``) are not
    flagged even if they might resolve to a private address.

    Args:
        url: The URL to check.

    Returns:
        True if the URL should be treated as a potential SSRF target,
        False otherwise.
    """
    result = is_loopback(url) or is_private(url) or is_link_local(url)
    if result:
        logging.debug('Potential SSRF target detected: %s', url)
    return result
