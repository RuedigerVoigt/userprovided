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


_DIGITS = {8: '01234567',
           10: '0123456789',
           16: '0123456789abcdefABCDEF'}


def _parse_ipv4_part(part: str) -> int | None:
    """Parse one dot-separated part of an IPv4 address the way inet_aton does.

    The base is taken from the prefix: ``0x`` means hexadecimal, a leading
    zero means octal, anything else is decimal.

    Returns the value, or None if the part is not a number in that base.
    """
    if part[:2].lower() == '0x':
        digits, base = part[2:], 16
    elif len(part) > 1 and part[0] == '0':
        digits, base = part[1:], 8
    else:
        digits, base = part, 10
    # int() would also accept underscores, signs and surrounding whitespace,
    # none of which inet_aton allows.
    if not digits or not all(c in _DIGITS[base] for c in digits):
        return None
    return int(digits, base)


def _parse_ipv4(host: str) -> ipaddress.IPv4Address | None:
    """Parse an IPv4 address in any of the encodings inet_aton accepts.

    ``ipaddress.ip_address()`` only accepts four dotted decimal octets, but
    the C library parser behind most HTTP clients and OS network stacks is
    far more permissive: it takes one to four parts, each in decimal, octal
    or hexadecimal, where the final part fills every octet the earlier parts
    left over. All of the following therefore reach 127.0.0.1:

    * ``2130706433``, ``0x7f000001``, ``017700000001`` (one part)
    * ``127.1`` (two parts), ``127.0.1`` (three parts)
    * ``0177.0.0.1``, ``0x7f.0.0.1`` (mixed per-part bases)

    A guard that only calls ``ipaddress.ip_address(host)`` treats every one
    of them as a hostname rather than an address, and so reports an internal
    target as safe.

    Returns an IPv4Address on success, None if the host is not an IPv4
    address in any of these encodings.
    """
    parts = host.split('.')
    if len(parts) > 4:
        return None
    values: list[int] = []
    for part in parts:
        value = _parse_ipv4_part(part)
        if value is None:
            return None
        values.append(value)
    # Every part but the last is a single octet; the last one covers the rest.
    if any(value > 255 for value in values[:-1]):
        return None
    if values[-1] >= 1 << (8 * (5 - len(parts))):
        return None
    packed = values[-1]
    for index, value in enumerate(values[:-1]):
        packed |= value << (8 * (3 - index))
    return ipaddress.IPv4Address(packed)


def _parse_ip(host: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    """Try to parse a host string as an IP address, including alternate encodings.

    Returns an IPv4Address/IPv6Address on success, None if the host is not
    a recognised IP address in any encoding. See :func:`_parse_ipv4` for the
    IPv4 encodings that are accepted beyond plain dotted decimal.
    """
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        pass
    return _parse_ipv4(host)


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

    IPv4 hosts are recognised in every encoding the C library parser
    accepts, so ``127.1``, ``0x7f000001`` and ``0177.0.0.1`` are flagged
    just like ``127.0.0.1``.

    Warning:
        This function does **not** perform DNS resolution, so a False
        result is not authorization to connect. A hostname that is not an
        IP address (other than ``localhost`` and ``.local``) is never
        flagged, however it resolves. Callers who need an actual guarantee
        must resolve the host themselves, reject every non-global address
        in the result, connect to that validated address rather than
        re-resolving the name, and re-check each redirect.

    A URL whose host cannot be determined — because it is malformed, or
    carries no host at all — is reported as a potential target.

    Args:
        url: The URL to check.

    Returns:
        True if the URL should be treated as a potential SSRF target,
        False otherwise.

    Raises:
        TypeError: If url is not a string.
    """
    host = _host_from_url(url)
    if host is None:
        # Unlike the predicates above, this is a guard: callers fetch the URL
        # when it answers False. "I cannot tell" must therefore not be
        # answered with "safe".
        logging.debug('No host to check, treating as potential SSRF target: %r',
                      url)
        return True

    if is_loopback(url) or is_private(url) or is_link_local(url):
        logging.debug('Potential SSRF target detected: %r', url)
        return True

    # RFC 6598 carrier-grade NAT is not covered by is_private above.
    ip = _parse_ip(host)
    if ip is not None and ip in _CGNAT_NETWORK:
        logging.debug('Potential SSRF target detected (CGNAT): %r', url)
        return True

    return False
