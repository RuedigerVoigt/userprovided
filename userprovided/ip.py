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


# RFC 6598 carrier-grade NAT ("shared address space"). Python's
# ``ipaddress.is_private`` does NOT classify this range as private, but it is
# routinely used inside cloud and carrier networks, so it is a realistic
# internal target for SSRF. The guard below therefore treats it as unsafe.
_CGNAT_NETWORK = ipaddress.ip_network('100.64.0.0/10')


def _parse_ip(host: str):
    """Try to parse a host string as an IP address, including alternate encodings.

    ``ipaddress.ip_address()`` only accepts standard dotted-decimal notation.
    However, many HTTP clients and operating-system network stacks also accept
    alternate integer encodings of IPv4 addresses:

    * Decimal integer: ``2130706433`` == 127.0.0.1
    * 0x-prefixed hex: ``0x7f000001`` == 127.0.0.1
    * Old-style octal:  ``017700000001`` == 127.0.0.1

    An attacker can use any of these to bypass a guard that only calls
    ``ipaddress.ip_address(host)`` directly, because that call raises
    ``ValueError`` for non-dotted strings and the guard then returns False
    (not an SSRF target).  This function tries all three encodings before
    giving up, so the SSRF check is not bypassable by encoding tricks.

    Known limitation: mixed per-octet encodings such as ``0x7f.0.0.1`` or
    ``0177.0.0.1`` are not handled, as they require per-octet base detection.
    Some HTTP clients (e.g. curl) accept these forms, so callers should be
    aware the guard is not exhaustive.

    Returns an IPv4Address/IPv6Address on success, None if the host is not
    a recognised IP address in any encoding.
    """
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        pass
    # Decimal integer or 0x-prefixed hex
    try:
        return ipaddress.ip_address(int(host, 0))
    except (ValueError, OverflowError):
        pass
    # Old-style octal: starts with 0, remaining chars are octal digits
    if len(host) > 1 and host[0] == '0' and all(c in '01234567' for c in host[1:]):
        try:
            return ipaddress.ip_address(int(host, 8))
        except (ValueError, OverflowError):
            pass
    return None


def is_loopback(url: str) -> bool:
    """Check whether the host in a URL resolves to a loopback address.

    Returns True for IP addresses in the loopback range (127.0.0.0/8 for
    IPv4, ::1 for IPv6) and for the hostname ``localhost``.

    Args:
        url: The URL whose host to check.

    Returns:
        True if the host is a loopback address or ``localhost``,
        False otherwise (including malformed URLs).

    Raises:
        TypeError: If url is not a string.
    """
    host = _host_from_url(url)
    if host is None:
        return False
    if host == 'localhost':
        return True
    ip = _parse_ip(host)
    return ip.is_loopback if ip is not None else False


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

    Raises:
        TypeError: If url is not a string.
    """
    host = _host_from_url(url)
    if host is None:
        return False
    ip = _parse_ip(host)
    return ip.is_private if ip is not None else False


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

    Raises:
        TypeError: If url is not a string.
    """
    host = _host_from_url(url)
    if host is None:
        return False
    if host.endswith('.local'):
        return True
    ip = _parse_ip(host)
    return ip.is_link_local if ip is not None else False


def is_potential_ssrf_target(url: str) -> bool:
    """Check whether a URL is a potential SSRF (Server-Side Request Forgery) target.

    Returns True if the URL's host is a loopback address, a private IP,
    or a link-local address. This covers the most common internal targets
    an attacker would attempt to reach via SSRF:

    * Loopback: 127.0.0.0/8, ::1, ``localhost``
    * Private (RFC 1918): 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
    * Link-local: 169.254.0.0/16 (incl. cloud metadata at 169.254.169.254),
      fe80::/10, ``.local`` hostnames

    It also flags the RFC 6598 carrier-grade NAT range (100.64.0.0/10),
    which ``ipaddress`` does not consider private but which is a realistic
    internal target inside cloud and carrier networks.

    This function does **not** perform DNS resolution. Hostnames that are
    not IP addresses (other than ``localhost`` and ``.local``) are not
    flagged even if they might resolve to a private address.

    Args:
        url: The URL to check.

    Returns:
        True if the URL should be treated as a potential SSRF target,
        False otherwise.

    Raises:
        TypeError: If url is not a string.
    """
    if is_loopback(url) or is_private(url) or is_link_local(url):
        logging.debug('Potential SSRF target detected: %r', url)
        return True

    # RFC 6598 carrier-grade NAT is not covered by is_private above.
    host = _host_from_url(url)
    if host is not None:
        ip = _parse_ip(host)
        if ip is not None and ip in _CGNAT_NETWORK:
            logging.debug('Potential SSRF target detected (CGNAT): %r', url)
            return True

    return False
