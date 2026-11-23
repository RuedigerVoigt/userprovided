"""
URL related functions of the userprovided library
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
Copyright (c) 2020-2026 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""


# python standard library:
import ipaddress
import logging
import mimetypes
import posixpath
import re
import unicodedata
import urllib.parse

from userprovided import err


logger = logging.getLogger(__name__)

# Practical upper bound for URL length. No hard RFC limit exists, but most
# HTTP servers and browsers reject URLs beyond 2048–8192 characters.
# Accepting arbitrarily long strings risks slow regex processing and memory use.
_MAX_URL_LENGTH = 2048
_TRAILING_DOTS_AND_SPACE = re.compile(r'[\s.]+\Z')
# Forbidden domain code points of the WHATWG URL Standard that urlparse can
# leave in a hostname, plus all Unicode whitespace: IDNA maps characters like
# U+3000 to a space. '%' is handled separately, see _browser_reads_other_host.
_FORBIDDEN_HOST_CHAR = re.compile(r'[\s\x00-\x1f\x7f<>\\^|]')
# What a non-ASCII host may consist of after it was mapped to ASCII.
_MAPPED_HOST = re.compile(r'[a-z0-9._-]+')
# The deviation characters of UTS #46: the stdlib codec (IDNA 2003) maps them
# away, browsers keep them, so 'straße' and 'strasse' are two hosts.
_IDNA_DEVIATIONS = frozenset('ßς‌‍')
_COMPRESSION_SUFFIXES = frozenset({'.gz', '.z', '.bz2', '.xz', '.br'})
# WHATWG "special" schemes: their parser reads '\' as '/' and percent-decodes
# the host.
_SPECIAL_SCHEMES = frozenset({'ftp', 'file', 'http', 'https', 'ws', 'wss'})
# The WHATWG default ports. 'file' has none.
_DEFAULT_PORTS = {'ftp': 21, 'http': 80, 'https': 443, 'ws': 80, 'wss': 443}

# Known 2-part TLDs (country code second-level domains).
# This is a hand-maintained subset of the most common ones, because full
# coverage means shipping the Public Suffix List (https://publicsuffix.org/)
# and this package relies solely on the Standard Library. Under a suffix that
# is missing here, one label too few is kept: 'alice.com.ua' resolves to
# 'com.ua', so unrelated sites share a registrable domain. Callers needing
# full coverage should use a dedicated package such as tldextract.
TWO_PART_TLDS = {
    # United Kingdom
    'co.uk', 'gov.uk', 'ac.uk', 'org.uk', 'net.uk',
    # Japan
    'co.jp', 'ne.jp', 'or.jp', 'go.jp', 'ac.jp',
    # Australia
    'com.au', 'net.au', 'org.au', 'edu.au', 'gov.au',
    # New Zealand
    'co.nz', 'net.nz', 'org.nz', 'ac.nz', 'govt.nz',
    # South Africa
    'co.za', 'net.za', 'org.za', 'gov.za', 'ac.za',
    # India
    'co.in', 'net.in', 'org.in', 'gen.in', 'firm.in',
    # Brazil
    'com.br', 'net.br', 'org.br', 'gov.br', 'edu.br',
    # China
    'com.cn', 'net.cn', 'org.cn', 'gov.cn', 'edu.cn',
    # Mexico
    'com.mx', 'net.mx', 'org.mx', 'gob.mx', 'edu.mx',
    # Singapore
    'com.sg', 'net.sg', 'org.sg', 'gov.sg', 'edu.sg',
    # Hong Kong
    'com.hk', 'net.hk', 'org.hk', 'gov.hk', 'edu.hk',
    # Turkey
    'com.tr', 'net.tr', 'org.tr', 'gen.tr', 'edu.tr',
    # Israel
    'co.il', 'ac.il', 'org.il', 'net.il', 'gov.il',
    # South Korea
    'co.kr', 'ne.kr', 'or.kr', 're.kr', 'go.kr',
    # Argentina
    'com.ar', 'net.ar', 'org.ar', 'gov.ar', 'edu.ar',
    # Poland
    'com.pl', 'net.pl', 'org.pl', 'gov.pl', 'edu.pl',
    # Thailand
    'co.th', 'in.th', 'go.th', 'ac.th', 'or.th',
    # Vietnam
    'com.vn', 'net.vn', 'org.vn', 'gov.vn', 'edu.vn',
    # Austria
    'co.at', 'or.at', 'gv.at', 'ac.at',
    # Hungary
    'co.hu', 'org.hu', 'gov.hu', 'edu.hu',
}


_DIGITS = {8: '01234567',
           10: '0123456789',
           16: '0123456789abcdefABCDEF'}


def _parse_ipv4_part(part: str) -> int | None:
    """Parse one dot-separated part of an IPv4 address the way inet_aton does.

    The base is taken from the prefix: ``0x`` means hexadecimal, a leading
    zero means octal, anything else is decimal. ``0x`` alone is zero.

    Returns the value, or None if the part is not a number in that base.
    """
    if part[:2].lower() == '0x':
        digits, base = part[2:], 16
        if not digits:
            # Browsers and glibc read it as 0, so 'http://0x/' is 0.0.0.0.
            return 0
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


def _is_ip_address(host: str) -> bool:
    """True if host is an IP address, including the IPv4 forms of inet_aton."""
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return _parse_ipv4(host) is not None
    return True


def _map_to_ascii(host: str) -> str | None:
    """Map a non-ASCII host to the lowercase ASCII form clients resolve.

    Returns None if the host cannot be mapped.
    """
    # NFKC first, as the codec only knows the mappings of Unicode 3.2.
    try:
        return unicodedata.normalize('NFKC', host).encode('idna').decode('ascii').lower()
    except UnicodeError:
        return None


def _ends_in_number(host: str) -> bool:
    """True if the WHATWG URL Standard must parse host as IPv4.

    That is the case if the last label, ignoring a trailing dot, is a
    decimal number or ``0x`` followed by hexadecimal digits.
    """
    labels = host.split('.')
    if labels[-1] == '' and len(labels) > 1:
        labels.pop()
    last = labels[-1]
    if last[:2] == '0x':
        return all(c in _DIGITS[16] for c in last[2:])
    return last != '' and all(c in _DIGITS[10] for c in last)


def _bracketed_host_is_not_ipv6(parsed: urllib.parse.ParseResult) -> bool:
    """True if the host is in square brackets but is no IPv6 address."""
    # urlparse strips the brackets and accepts the IPvFuture form: '[v1.x]'
    # becomes 'v1.x', a different host. Browsers only accept IPv6 there.
    if '[' not in parsed.netloc.rpartition('@')[2]:
        return False
    try:
        ipaddress.IPv6Address(parsed.hostname or '')
    except ValueError:
        return True
    return False


def _browser_host_problem(parsed: urllib.parse.ParseResult) -> str | None:
    """Why browsers would read a different host than urlparse, or none.

    Returns None if they read the same host.
    """
    if _bracketed_host_is_not_ipv6(parsed):
        return 'URL host in brackets is no IPv6 address.'
    if parsed.scheme not in _SPECIAL_SCHEMES:
        return None
    # Browsers end the authority at the backslash, urlparse does not:
    # 'http://evil.com\@good.com' goes to evil.com, urlparse says good.com.
    if '\\' in parsed.netloc:
        return 'URL has a backslash in the authority.'
    host = parsed.hostname or ''
    # Browsers also percent-decode the host: 'http://%31%32%37.0.0.1' goes
    # to 127.0.0.1, urlparse keeps the escapes.
    if '%' in host:
        return 'URL host is percent-encoded.'
    if not host.isascii():
        # Browsers map the host to ASCII before they look for a number.
        host = _map_to_ascii(host) or ''
    # Browsers read such a host as IPv4 or reject it: 'http://1.2.3.999/'.
    # Not an IPv6 literal, though: '::ffff:192.0.2.1' ends in a number too.
    if (':' not in host and _ends_in_number(host)
            and _parse_ipv4(host.removesuffix('.')) is None):
        return 'URL host ends in a number but is no IPv4 address.'
    return None


def _host_from_url(url: str) -> str | None:
    """Extract the lowercase hostname from a URL, or None on failure.

    Raises:
        TypeError: If url is not a string. A non-string is a caller error,
            not a URL that failed to parse, so it is surfaced rather than
            swallowed into a None return.
    """
    if not isinstance(url, str):
        raise TypeError('URL must be a string.')
    # Deliberately no length limit: the SSRF guard in ip.py builds on this,
    # and padding the query string must not hide the host from it.
    try:
        parsed = urllib.parse.urlparse(url.strip())
        host = parsed.hostname
    except Exception:
        return None
    if not host or _FORBIDDEN_HOST_CHAR.search(host):
        return None
    if parsed.scheme in _SPECIAL_SCHEMES and '\\' in parsed.netloc:
        # See _browser_host_problem.
        return None
    if _bracketed_host_is_not_ipv6(parsed):
        return None
    if not host.isascii():
        # Clients map such a host to ASCII before they resolve it:
        # '１２７.0.0.1', '127。0。0。1' and 'local\xadhost' all reach loopback.
        mapped = _map_to_ascii(host)
        # A mapping can produce delimiters ('＋' -> '+') that clients treat
        # differently, so the target cannot be told.
        if mapped is None or not _MAPPED_HOST.fullmatch(mapped):
            return None
        host = mapped
    if '%' in host and ':' not in host:
        # Browsers percent-decode the host, other clients may too, so the
        # SSRF guard cannot tell the target. This applies to any scheme.
        # IPv6 literals are exempt: there '%' starts a zone ID, which the
        # ipaddress module parses ('fe80::1%eth0' stays link-local).
        return None
    # A single trailing dot denotes the DNS root and is resolved away, so
    # "localhost." reaches the same host as "localhost". Without this the
    # SSRF guard in ip.py would not recognise the dotted form.
    host = host.removesuffix('.')
    if ':' not in host and _ends_in_number(host) and _parse_ipv4(host) is None:
        # Browsers read such a host as IPv4. If the parser here cannot, a
        # client may still reach some address, so the target cannot be told.
        return None
    return host.lower() if host else None


def is_url(url: str,
           require_specific_schemes: tuple | str | None = None) -> bool:
    """Validates basic URL format without attempting connection.

    Performs basic structural validation of a URL including scheme and
    network location presence. Optionally restricts to specific schemes.
    A host containing whitespace, control characters or one of
    ``< > \\ ^ |`` is invalid, and so is anything but an IPv6 address in
    square brackets. In an http(s), ws(s), ftp or file URL, so is a
    backslash in the authority, a ``%`` in the host, and a host whose last
    label is a number but that is no IPv4 address (``1.2.3.999``). The
    ``%`` rule includes IPv6 zone IDs (``http://[fe80::1%25eth0]/``), which
    browsers reject. Surrounding whitespace is ignored.

    Args:
        url: The URL string to validate.
        require_specific_schemes: Tuple of allowed schemes (e.g., ('http', 'https')).
            A plain string is treated as a single scheme name.
            If None, any scheme is allowed. Defaults to None.

    Returns:
        True if URL has valid basic structure, False otherwise.

    Raises:
        TypeError: If url is not a string.
    """
    if not isinstance(url, str):
        raise TypeError('URL must be a string.')

    if len(url) > _MAX_URL_LENGTH:
        logger.debug('URL exceeds maximum length of %d characters.', _MAX_URL_LENGTH)
        return False

    try:
        # strip: urlparse drops leading whitespace itself, but keeps trailing
        # whitespace in the hostname ('http://example.com ').
        parsed = urllib.parse.urlparse(url.strip())
    except ValueError:
        # urllib raises for malformed input like an unclosed IPv6 literal
        # ('http://[::1'). Classifying a URL as invalid is what this function
        # is for, so return False instead of raising at the caller.
        logger.debug('URL could not be parsed.')
        return False

    if parsed.scheme == '':
        logger.debug('The URL has no scheme (like http or https)')
        return False
    if require_specific_schemes:
        if isinstance(require_specific_schemes, str):
            # A bare string would be checked with substring matching:
            # 'http' in 'https' is True, so ('https') — a string, not a
            # tuple — would accept http URLs. Treat it as one scheme name.
            require_specific_schemes = (require_specific_schemes,)
        if parsed.scheme not in require_specific_schemes:
            logger.debug('Scheme %r not supported.', parsed.scheme)
            return False

    # hostname, not netloc: netloc also carries userinfo and port, so
    # 'http://user@/path' and 'http://:8080/path' have one but no host.
    if parsed.hostname is None:
        logger.debug('URL has no host.')
        return False
    if _FORBIDDEN_HOST_CHAR.search(parsed.hostname):
        logger.debug('URL host contains a forbidden character.')
        return False
    problem = _browser_host_problem(parsed)
    if problem:
        logger.debug(problem)
        return False

    try:
        # urllib validates the port lazily, on attribute access. Without this
        # a URL no client could ever dial ('https://example.com:notaport',
        # or a port above 65535) would be reported as valid.
        parsed.port
    except ValueError:
        logger.debug('URL has an invalid port.')
        return False

    return True


def _normalize_query_part(query: str,
                          drop_keys: list | tuple | set | str | None = None
                          ) -> str:
    """Normalizes URL query parameters for consistent formatting.

    Processes query parameters by removing empty values, sorting alphabetically,
    and optionally filtering out specified keys. Preserves legacy query formats
    that don't follow key=value syntax.

    Args:
        query: Query string to normalize (without leading '?').
        drop_keys: Collection of parameter keys to remove from the query.
            Can be list, tuple, or set. A plain string is treated as a
            single key. Defaults to None.

    Returns:
        Normalized query string with parameters sorted alphabetically.

    Raises:
        QueryKeyConflict: If duplicate keys have conflicting values.
    """
    if isinstance(drop_keys, str):
        # A bare string would be checked with substring matching: ('utm') —
        # a string, not a tuple — would also drop the keys 'u', 't' and 'm'.
        drop_keys = (drop_keys,)

    if '=' not in query:
        # RFC 3986 prescribes a key=value syntax, but some old implementations
        # do not follow that and generate URLs like:
        # https://www.example.com/forums/forumdisplay.php?example-forum
        # In this case the query part is not changed.
        return query

    chunks = query.split('&')
    keep: dict[str, str] = dict()
    for chunk in chunks:
        if chunk != '' and '=' in chunk:
            split_chunk = chunk.split('=', 1)
            key = split_chunk[0]
            value = split_chunk[1]
            if key != '' and value != '':
                if key in keep:
                    # i.e. we already processed the same key
                    if keep[key] != value:
                        raise err.QueryKeyConflict(
                            'Duplicate URL query key with conflicting values')
                    logger.debug(
                        'Duplicate key in URL query part, but no conflict.')
                elif drop_keys and key in drop_keys:
                    # i.e. the key is in the list of keys to drop
                    pass
                else:
                    keep[key] = value
    ordered = list()
    if keep:
        for key in sorted(keep):
            ordered.append(f"{key}={keep[key]}")

    return '&'.join(ordered) if ordered else ''


def normalize_url(url: str,
                  drop_keys: list | tuple | set | str | None = None,
                  do_not_change_query_part: bool = False) -> str:
    """Normalizes a URL to a canonical format.

    Performs comprehensive URL normalization including:
    - Remove whitespace around the URL
    - Convert scheme and hostname to lowercase
    - Remove standard ports (80 for HTTP, 443 for HTTPS)
    - Remove duplicate slashes from the path
    - Remove fragments (like #foo)
    - Remove empty query parameters
    - Sort query parameters alphabetically
    - Optionally remove specified query keys (e.g., tracking parameters)
    - Drop any embedded credentials (``user:password@`` userinfo)

    Args:
        url: The URL to normalize.
        drop_keys: Collection of query parameter keys to remove.
            Can be list, tuple, or set. A plain string is treated as a
            single key. Defaults to None.
        do_not_change_query_part: If True, preserves original query format
            to avoid issues with legacy systems using duplicate keys.
            Defaults to False.

    Returns:
        Normalized URL string with consistent formatting.

    Raises:
        TypeError: If url is not a string.
        ValueError: If the URL is malformed.
        ContradictoryParameters: If both drop_keys and do_not_change_query_part
            are specified.
        QueryKeyConflict: If the query repeats a key with conflicting values
            and do_not_change_query_part is False.
    """
    if not isinstance(url, str):
        raise TypeError('URL must be a string.')

    url = url.strip()

    if not is_url(url):
        raise ValueError('Malformed URL')

    if drop_keys and do_not_change_query_part:
        raise err.ContradictoryParameters(
            'Cannot drop keys AND leave the query part unchanged.')

    # Remove fragments (https://www.example.com#foo -> https://www.example.com)
    url, _ = urllib.parse.urldefrag(url)

    standard_ports = {'http': 80, 'https': 443}

    parsed = urllib.parse.urlparse(url)
    reassemble = list()
    reassemble.append(parsed.scheme.lower())

    # is_url above rejects a port urllib cannot cast, so this cannot raise.
    port = parsed.port

    host = parsed.hostname
    if host is None:  # pragma: no cover
        # is_url above rejects a URL without a host. This narrows the type;
        # without it None was reassembled as 'http:///' or 'http://None:8080'.
        raise ValueError('Malformed URL')
    if ':' in host:
        # urlparse strips the square brackets from IPv6 literals.
        # Restore them, otherwise the reassembled URL is invalid.
        host = f"[{host}]"

    if not port:
        # There is no port to begin with
        # hostname is lowercase without port
        reassemble.append(host)
    elif (parsed.scheme in standard_ports and
            port == standard_ports[parsed.scheme]):
        # There is a port and it equals the standard.
        # That means it is redundant.
        reassemble.append(host)
    else:
        # There is a port but it is not in the list or not standard
        reassemble.append(f"{host}:{port}")

    # remove common typo (// in path element). str.replace consumes
    # non-overlapping matches, so a single pass turns '///a' into '//a' and
    # leaves a duplicate behind. Collapse any run of slashes in one step,
    # otherwise '//a' and '///a' -- the same resource -- yield two keys.
    reassemble.append(re.sub('/{2,}', '/', parsed.path))

    # do not change parameters of the path element (!= query)
    reassemble.append(parsed.params)

    if do_not_change_query_part:
        reassemble.append(parsed.query)
    else:
        reassemble.append(_normalize_query_part(parsed.query, drop_keys))

    # urlunparse expects a fifth element (the already removed fragment)
    reassemble.append('')

    url = urllib.parse.urlunparse(reassemble)

    return url


def normalize_hostname(host: str) -> str:
    """Normalize a bare hostname or IP literal to one canonical form.

    Different spellings of the same host (trailing root-label dot,
    internationalized vs. punycode names, compressed vs. expanded IPv6)
    are reduced to a single canonical string, suitable as an identity
    key (e.g. for rate limiting or deduplication). Normalization steps:

    - Strip surrounding whitespace and lowercase.
    - Remove trailing root-label dots ('example.com.' -> 'example.com').
    - IP literals (IPv6 with or without square brackets, IPv4) are
      canonicalized via the ipaddress module: '[::1]', '::1', and
      '0:0:0:0:0:0:0:1' all become '::1'. The returned form carries
      no brackets. The short, octal and hexadecimal IPv4 forms that
      browsers accept ('127.1', '0x7f.0.0.1', '2130706433') become
      dotted decimal ('127.0.0.1').
    - Non-ASCII hostnames are canonicalized to punycode via the stdlib
      IDNA codec ('münchen.example' -> 'xn--mnchen-3ya.example'). The
      stdlib codec implements IDNA 2003, so a handful of newer scripts
      and codepoints differ from IDNA 2008 — acceptable best-effort.
      If the codec cannot encode the name, the lowercased unicode form
      is returned instead of raising.
    - ASCII hostnames pass through unchanged (lowercased, dot-stripped).
      This is a normalizer, not a validator: label syntax is not checked.

    Normalization is idempotent: feeding the result back in returns it
    unchanged. In contrast to this function, ``normalize_url`` and
    ``extract_domain`` deliberately do not canonicalize hosts, as their
    outputs serve as identity keys in existing downstream databases.

    Args:
        host: A bare hostname or IP literal — not a URL.

    Returns:
        The canonical form of the hostname or IP address.

    Raises:
        TypeError: If host is not a string.
        ValueError: If host is empty, whitespace-only, a bare dot,
            empty brackets, or longer than 2048 characters.
    """
    if not isinstance(host, str):
        raise TypeError('Hostname must be a string.')

    if len(host) > _MAX_URL_LENGTH:
        raise ValueError(
            f"Hostname exceeds maximum length of {_MAX_URL_LENGTH} characters.")

    # Whitespace and dots together: stripped one after the other,
    # 'example.com .' kept its space ('example.com ').
    candidate = _TRAILING_DOTS_AND_SPACE.sub('', host.strip().lower())

    unbracketed = candidate
    if candidate.startswith('[') and candidate.endswith(']'):
        unbracketed = candidate[1:-1]

    if not unbracketed:
        raise ValueError('Hostname is empty.')

    try:
        return str(ipaddress.ip_address(unbracketed))
    except ValueError:
        # Not an IP literal, continue with hostname handling
        pass

    ipv4 = _parse_ipv4(unbracketed)
    if ipv4 is not None:
        return str(ipv4)

    if not candidate.isascii():
        try:
            encoded = candidate.encode('idna').decode('ascii')
        except UnicodeError:
            logger.debug(
                'Hostname could not be IDNA-encoded. '
                'Returning the lowercased unicode form.')
        else:
            # Normalize the ASCII result once more, or the output is not
            # idempotent: the codec turns '。' and '⒈' into dots after the
            # trailing dots were stripped ('example.com。' -> 'example.com.'),
            # and drops invisible characters ('[::1]\xad' -> '[::1]').
            return normalize_hostname(encoded)

    return candidate


def extract_domain_from_host(host: str, drop_subdomain: bool = False) -> str:
    """Extract the domain from a bare hostname instead of a full URL.

    Host-level sibling of ``extract_domain`` for callers that already
    hold a hostname and would otherwise have to fabricate a URL around
    it. Unlike ``extract_domain``, which deliberately does not
    canonicalize hosts (its output is an identity key in existing
    downstream databases), this function normalizes its input via
    ``normalize_hostname`` first (trailing dot, IDNA, IP
    canonicalization).

    Args:
        host: A bare hostname or IP literal — not a URL.
        drop_subdomain: If True, extracts only the registrable domain
            (domain + public suffix), removing subdomains. Handles
            multi-part TLDs correctly (e.g., .co.uk, .com.au).

    Returns:
        The normalized domain. IP addresses (which have no subdomains
        or public suffix) and single-word hosts like 'localhost' are
        returned in canonical form regardless of drop_subdomain.

    Raises:
        TypeError: If host is not a string.
        ValueError: If host is empty or longer than 2048 characters.

    Examples:
        >>> extract_domain_from_host('www.example.co.uk', drop_subdomain=True)
        'example.co.uk'
        >>> extract_domain_from_host('MÜNCHEN.example.')
        'xn--mnchen-3ya.example'
        >>> extract_domain_from_host('[::1]')
        '::1'
    """
    normalized = normalize_hostname(host)

    if drop_subdomain:
        # The helper returns IP addresses and single-word hosts as-is.
        return _extract_registrable_domain(normalized, TWO_PART_TLDS)

    return normalized


def extract_host(url: str, *, with_port: bool = False) -> str:
    """Extract the canonical host of a URL, optionally with its port.

    Meant as an identity key (rate limiting, deduplication, per-host
    accounting): every spelling of a host yields the same key, and a URL
    whose host cannot be told unambiguously raises instead of being keyed
    under the wrong host. Unlike ``extract_domain``, which deliberately
    does not canonicalize, the host is normalized the way
    ``normalize_hostname`` does it (lowercase, trailing dots, punycode, IP
    addresses in canonical form). Userinfo is ignored.

    The URL may be of any length: unlike ``is_url``, a long path or query
    does not make it invalid. The host is rejected for everything
    ``is_url`` rejects, and in addition for a ``%`` in the host of any
    scheme (outside an IPv6 zone ID), for a non-ASCII host that has no
    ASCII form or whose ASCII form contains other characters than letters,
    digits, ``.``, ``-`` and ``_``, and for a host containing ``ß``, ``ς``
    or a zero-width (non-)joiner, which browsers keep but the stdlib IDNA
    codec maps away (``straße`` would become ``strasse``).

    Args:
        url: The URL. It needs a scheme and a host.
        with_port: If True, return ``host:port`` with the port the URL
            addresses: the one given, or else the default of the scheme
            (http and ws 80, https and wss 443, ftp 21). A scheme without
            a default and without a port yields the host alone. IPv6
            addresses are put in square brackets. Defaults to False.

    Returns:
        The canonical host, or ``host:port`` if with_port is True. An IPv6
        address carries no brackets unless with_port is True.

    Raises:
        TypeError: If url is not a string.
        ValueError: If the URL cannot be parsed, has no scheme or no host,
            has an invalid port, or its host cannot be told unambiguously.

    Examples:
        >>> extract_host('https://WWW.Example.com./path?q=1')
        'www.example.com'
        >>> extract_host('https://example.com/', with_port=True)
        'example.com:443'
        >>> extract_host('http://[0:0:0:0:0:0:0:1]:8080/', with_port=True)
        '[::1]:8080'
        >>> extract_host('https://münchen.example/')
        'xn--mnchen-3ya.example'
        >>> extract_host('http://127.1/')
        '127.0.0.1'
    """
    if not isinstance(url, str):
        raise TypeError('URL must be a string.')

    # No length limit: padding the path or query must not hide the host.
    try:
        parsed = urllib.parse.urlparse(url.strip())
    except ValueError as e:
        raise ValueError('URL could not be parsed.') from e

    if not parsed.scheme:
        raise ValueError('URL has no scheme.')
    raw_host = parsed.hostname
    if not raw_host:
        raise ValueError('URL has no host.')
    if _FORBIDDEN_HOST_CHAR.search(raw_host):
        raise ValueError('URL host contains a forbidden character.')
    problem = _browser_host_problem(parsed)
    if problem:
        raise ValueError(problem)
    if '%' in raw_host and ':' not in raw_host:
        # is_url allows this outside the special schemes, but a client may
        # still decode it, so 'foo://ex%61mple/' could be 'foo://example/'.
        raise ValueError('URL host is percent-encoded.')
    if _IDNA_DEVIATIONS.intersection(raw_host):
        raise ValueError('URL host contains a character that IDNA versions '
                         'map differently.')

    try:
        port = parsed.port
    except ValueError as e:
        raise ValueError('URL has an invalid port.') from e

    host = normalize_hostname(raw_host)
    if not raw_host.isascii() and not _MAPPED_HOST.fullmatch(host):
        # Either the IDNA codec failed and the host stayed non-ASCII, or the
        # mapping produced a delimiter ('＋' -> '+') clients treat differently.
        raise ValueError('URL host has no unambiguous ASCII form.')

    if not with_port:
        return host
    if ':' in host:
        host = f'[{host}]'
    if port is None:
        port = _DEFAULT_PORTS.get(parsed.scheme)
    return host if port is None else f'{host}:{port}'


def determine_file_extension(url: str,
                             provided_mime_type: str | None = None) -> str:
    """Determines appropriate file extension from URL and/or MIME type.

    Attempts to guess the correct file extension by analyzing the URL path
    and optionally using a provided MIME type as fallback. Handles cases
    where URLs lack extensions or have ambiguous formats. An extension in
    the URL that ``mimetypes`` recognizes is returned in lowercase,
    including a compression suffix (``.tar.gz``, or ``.gz`` alone if nothing
    recognized precedes it); ``.htm`` becomes ``.html``.

    Args:
        url: The URL to analyze for file extension hints.
        provided_mime_type: MIME type from server response headers.
            Used as fallback when URL doesn't provide clear extension.
            May be a full Content-Type value: parameters such as
            ``; charset=utf-8`` are ignored, and case does not matter.
            Defaults to None.

    Returns:
        File extension with leading dot (e.g., '.pdf', '.html') or
        '.unknown' if extension cannot be determined.

    Raises:
        TypeError: If url is not a string, or if provided_mime_type is
            neither a string nor None.
    """
    if not isinstance(url, str):
        raise TypeError('URL must be a string.')
    if provided_mime_type is not None and not isinstance(provided_mime_type,
                                                         str):
        raise TypeError('provided_mime_type must be a string or None.')

    if provided_mime_type:
        # A Content-Type header value carries parameters after the media
        # type (RFC 9110, section 8.3.1), which mimetypes does not recognize:
        # 'text/html; charset=utf-8' -> 'text/html'.
        # Type and subtype are case-insensitive: 'Text/HTML' -> 'text/html'.
        provided_mime_type = provided_mime_type.split(';', 1)[0].strip().lower()
    if provided_mime_type == '':
        provided_mime_type = None

    # Taken from the URL itself, not mapped back from the mime type:
    # that lost the compression suffix ('.tar.gz' -> '.tar') and
    # returned whatever extension the platform lists first for the type
    # (on Windows '.csv' -> '.xls').
    # Lowercased before any lookup: mimetypes matches compression suffixes
    # case-sensitively, so 'a.TAR.GZ' lost its '.tar'.
    try:
        path = urllib.parse.urlparse(url).path
    except ValueError:
        # Unparseable, like an unclosed IPv6 literal ('http://[::1/x.pdf'):
        # the URL gives no hint, so the mime type decides.
        logger.debug('URL %r could not be parsed.', url)
        path = ''
    base, extension = posixpath.splitext(path)
    extension = extension.lower()
    if extension in _COMPRESSION_SUFFIXES:
        # '.gz' and the like only name the compression.
        inner = posixpath.splitext(base)[1].lower()
        if mimetypes.guess_type('x' + inner)[0] is not None:
            extension = inner + extension
    elif (extension not in mimetypes.suffix_map
          and mimetypes.guess_type('x' + extension)[0] is None):
        extension = ''

    if extension:
        type_by_url = mimetypes.guess_type('x' + extension)[0]
        if (type_by_url is not None
                and provided_mime_type not in (None, type_by_url)):
            logger.debug('The mime type %r suggested by the URL %r does not '
                         'match the mime type supplied by the server (%r). '
                         'Using the extension in the URL.',
                         type_by_url, url, provided_mime_type)
    elif provided_mime_type is not None:
        # The URL does not contain an usable extension, but
        # the server provides a mime type.
        guessed = mimetypes.guess_extension(provided_mime_type)
        if guessed is None:
            logger.debug('No hint in URL and mime-type malformed for %r', url)
            return '.unknown'
        if guessed == '.bat' and provided_mime_type == 'text/plain':
            # text/plain is mapped to .bat in python 3.6.
            # Python 3.8 correctly guesses .txt as extension.
            return '.txt'
        extension = guessed
    else:
        # Neither the URL nor the server does hint to a extension
        logger.debug('Neither URL %r nor mime-type %r suggests a '
                     'file extension.', url, provided_mime_type)
        return '.unknown'

    if extension == '.htm':
        return '.html'

    return extension


def is_shortened_url(url: str) -> bool:
    """Check if a URL is from a known URL shortening service that allows random targets.
    Such URLs can be useful and harmless, but could also be a way for an attacker to
    disguise the target of a link.

    Args:
        url: The URL string to check.

    Returns:
        True if the URL is from a shortening service in the list, False otherwise.

    Raises:
        TypeError: If url is not a string.

    Note:
        This function checks against a list of popular URL shortening
        services. It will not detect all shortening services, especially
        custom domain shorteners or newer services.
        By design it will *not* recognize short URLs like youtu.be as
        they do not have random targets but the specific platform YouTube.
    """
    if not is_url(url):
        logger.debug('Invalid URL provided to shortened URL check')
        return False

    try:
        parsed = urllib.parse.urlparse(url)
        # hostname, not netloc: netloc carries the userinfo and the port, so
        # 'https://evil.com@bit.ly/' and 'https://bit.ly:443/' would both slip
        # past the lookup.
        # Normalized, or other spellings of the host slip past the lookup:
        # 'bit.ly.' and 'bit。ly' both resolve to bit.ly.
        domain = normalize_hostname(parsed.hostname or '')

        # Remove 'www.' prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]

        # Known URL shortening service domains
        shortener_domains = {
            'bit.ly', 'bitly.com',
            'tinyurl.com',
            't.co',  # https://help.x.com/en/using-x/url-shortener
            # EOL 09/2025: https://developers.googleblog.com/en/google-url-shortener-links-will-no-longer-be-available/
            'goo.gl',
            'lnkd.in',
            'ow.ly',
            'buff.ly',
            'short.link',
            'is.gd',
            'v.gd',
            'rebrand.ly',
            'tiny.cc',
            'shortened.com',
            'clicky.me',  # 08/2025 website says it is in "maintenace mode"
            'short.cm',
            'cutt.ly',
            'ur.ly',
            'short.io',
            'bl.ink',
            'u.to',
            'x.co',
            'shorturl.at',
            'trib.al'
        }

        return domain in shortener_domains

    except Exception:
        logger.debug('Error parsing URL for shortened URL detection')
        return False


def extract_domain(url: str, drop_subdomain: bool = False) -> str:
    """
    Extract the domain (hostname) from a URL and handle most important two level TLDs.

    This function deliberately does not canonicalize the host (trailing
    root-label dots, internationalized spellings, and equivalent IPv6
    literals stay as given): its output is an identity key in existing
    downstream databases and must remain stable. If you hold a bare
    hostname and want a canonical form, use ``extract_domain_from_host``,
    which normalizes via ``normalize_hostname``.

    Args:
        url: Full URL string (e.g., 'https://www.example.com:8080/path')
        drop_subdomain: If True, extracts only the registrable domain
                        (domain + public suffix), removing subdomains.
                        Handles the multi-part TLDs listed in TWO_PART_TLDS
                        (e.g., .co.uk, .com.au); see there for the limits of
                        that hand-maintained subset.
                        IP addresses and localhost are returned as-is.
                        A trailing root-label dot is removed, because the
                        registrable domain is a derived identity key and
                        'example.com.' must not be a second key for
                        'example.com'. Without drop_subdomain the host is
                        returned exactly as given, dot included.

    Returns:
        Domain string without port. For IP addresses (IPv4/IPv6) and localhost,
        returns the address/hostname unchanged.

    Raises:
        TypeError: If url is not a string.
        ValueError: If url is empty, its host contains whitespace, control
            characters or one of ``< > \\ ^ |``, its host is in square
            brackets but no IPv6 address, an http(s), ws(s), ftp or file URL
            has a backslash in the authority, a ``%`` in the host or a host
            that ends in a number but is no IPv4 address, or domain
            extraction fails.

    Examples:
        >>> extract_domain('https://www.example.com:8080/path')
        'www.example.com'
        >>> extract_domain('https://www.example.com', drop_subdomain=True)
        'example.com'
        >>> extract_domain('https://subdomain.example.co.uk/page', drop_subdomain=True)
        'example.co.uk'
        >>> extract_domain('https://www.example.com.au/page', drop_subdomain=True)
        'example.com.au'
        >>> extract_domain('http://192.168.1.1:8080/path', drop_subdomain=True)
        '192.168.1.1'
        >>> extract_domain('http://localhost:3000', drop_subdomain=True)
        'localhost'
    """
    if not isinstance(url, str):
        raise TypeError('URL must be a string.')

    if not url or not url.strip():
        raise ValueError("URL cannot be empty")

    if len(url) > _MAX_URL_LENGTH:
        raise ValueError(f"URL exceeds maximum length of {_MAX_URL_LENGTH} characters.")

    try:
        parsed = urllib.parse.urlparse(url.strip())
    except ValueError as e:
        # urllib rejects malformed input such as an unclosed IPv6 literal.
        raise ValueError("Invalid URL format.") from e
    domain = parsed.hostname

    if not domain:
        # netloc is deliberately not used as a fallback: it carries the
        # userinfo and the port, so 'http://user:pass@' would be handed back
        # as if it were a domain.
        raise ValueError("Could not extract domain from URL.")

    if _FORBIDDEN_HOST_CHAR.search(domain):
        # A host of spaces only was stripped to '' and returned as a domain.
        raise ValueError("URL host contains a forbidden character.")

    problem = _browser_host_problem(parsed)
    if problem:
        raise ValueError(problem)

    domain = domain.lower()

    if drop_subdomain:
        domain = _extract_registrable_domain(domain, TWO_PART_TLDS)

    return domain


def extract_tld(url: str) -> str:
    """
    Extract the TLD (top-level domain) from a URL.

    Correctly identifies 2-part TLDs (like .co.uk, .com.au) and returns them
    as a single unit. For standard TLDs (like .com, .org), returns just the
    single-part TLD.

    A trailing root-label dot is ignored, so the fully qualified
    'example.com.' reports the same TLD as 'example.com'.

    Args:
        url: Full URL string (e.g., 'https://www.example.com/path')

    Returns:
        TLD string with leading dot (e.g., '.com', '.co.uk', '.com.au').
        Returns empty string if TLD cannot be determined (e.g., for IP
        addresses, localhost, or invalid URLs).

    Raises:
        TypeError: If url is not a string.
        ValueError: If url is empty

    Examples:
        >>> extract_tld('https://www.example.com/path')
        '.com'
        >>> extract_tld('https://example.co.uk')
        '.co.uk'
        >>> extract_tld('https://subdomain.example.com.au/page')
        '.com.au'
        >>> extract_tld('https://www.example.com.')
        '.com'
        >>> extract_tld('http://192.168.1.1')
        ''
        >>> extract_tld('http://localhost')
        ''
    """
    if not isinstance(url, str):
        raise TypeError('URL must be a string.')

    if not url or not url.strip():
        raise ValueError("URL cannot be empty")

    if len(url) > _MAX_URL_LENGTH:
        raise ValueError(f"URL exceeds maximum length of {_MAX_URL_LENGTH} characters.")

    try:
        parsed = urllib.parse.urlparse(url.strip())
    except ValueError:
        # Same failure as in extract_domain, but this function reports "no TLD
        # could be determined" with an empty string instead of raising.
        return ''
    domain = parsed.hostname

    if (not domain or _FORBIDDEN_HOST_CHAR.search(domain)
            or _browser_host_problem(parsed)):
        # netloc is deliberately not used as a fallback -- see extract_domain.
        return ''

    # rstrip: a trailing root-label dot ('example.com.') is legal in a fully
    # qualified name and would otherwise be counted as an empty final label,
    # making every such host report '.' as its TLD.
    domain = domain.lower().rstrip('.')

    if not domain:
        # The host consisted of dots only.
        return ''

    # An IP address has no TLD. Its short forms count too: '127.1' has no TLD '.1'.
    if _is_ip_address(domain):
        return ''

    parts = domain.split('.')

    # Single-word domains (like localhost) have no TLD
    if len(parts) == 1:
        return ''

    # Check for 2-part TLD
    if len(parts) >= 2:  # pragma: no branch
        potential_2part_tld = '.'.join(parts[-2:])
        if potential_2part_tld in TWO_PART_TLDS:
            return '.' + potential_2part_tld

    # Standard single-part TLD
    return '.' + parts[-1]


def _extract_registrable_domain(domain: str, two_part_tlds: set) -> str:
    """
    Extract the registrable domain (domain + public suffix) from a full hostname.

    This removes subdomains while correctly handling 2-part TLDs, IP addresses,
    and special cases like localhost.

    Args:
        domain: Full domain/hostname (e.g., 'www.example.co.uk')
        two_part_tlds: Set of known 2-part TLDs (e.g., 'co.uk', 'com.au')

    Returns:
        Registrable domain (e.g., 'example.co.uk'), or the original domain
        for IP addresses and localhost.

    Algorithm:
        0. Remove trailing root-label dots so labels can be counted
        1. Check if domain is an IP address (IPv4 or IPv6) - return as-is
        2. Check if domain is localhost or single-word - return as-is
        3. Check for 2-part TLD match (e.g., .co.uk, .com.au)
        4. Fall back to simple single-part TLD (e.g., .com, .org)

    Examples:
        >>> _extract_registrable_domain('www.example.co.uk', TWO_PART_TLDS)
        'example.co.uk'
        >>> _extract_registrable_domain('subdomain.example.com', TWO_PART_TLDS)
        'example.com'
        >>> _extract_registrable_domain('deep.sub.example.com.au', TWO_PART_TLDS)
        'example.com.au'
        >>> _extract_registrable_domain('www.example.com.', TWO_PART_TLDS)
        'example.com'
        >>> _extract_registrable_domain('192.168.1.1', TWO_PART_TLDS)
        '192.168.1.1'
        >>> _extract_registrable_domain('localhost', TWO_PART_TLDS)
        'localhost'
    """
    # A trailing root-label dot is legal in a fully qualified name
    # ('www.example.com.') and produces an empty final label. Counting that
    # label collapses every such host onto its public suffix
    # ('www.example.com.' -> 'com.'), which makes unrelated sites share one
    # registrable domain. Strip the dots before splitting into labels.
    domain = domain.rstrip('.')

    # An IP address is returned as-is. Its short forms count too: '10.0.1'
    # is 10.0.0.1, not a subdomain of '0.1'.
    if _is_ip_address(domain):
        return domain

    parts = domain.split('.')

    if len(parts) <= 2:
        # Already a registrable domain or less (e.g., 'example.com' or 'localhost')
        return domain

    # Check for 2-part TLD (e.g., co.uk, com.au)
    if len(parts) >= 3:  # pragma: no branch
        potential_2part_tld = '.'.join(parts[-2:])
        if potential_2part_tld in two_part_tlds:
            # Return domain + 2-part TLD
            return '.'.join(parts[-3:])

    # Fall back to simple TLD (e.g., .com, .org)
    # Return last 2 parts (domain + TLD)
    return '.'.join(parts[-2:])


def url_matches_domain(url: str, domain: str) -> bool:
    """Check if a URL belongs to the specified domain.

    Extracts the registrable domain from the URL using ``extract_domain``
    with ``drop_subdomain=True`` and compares it to the given domain.
    This means all subdomains (including ``www.``) are resolved to the
    registrable domain before comparison.

    Trade-off / Security: Because all subdomains are collapsed, this function cannot
    distinguish ``www.example.com`` from ``sub.example.com`` — both match
    ``example.com``. If you need to match a specific subdomain, use
    ``extract_domain`` directly and compare the full hostname.

    Trade-off / Security: The registrable domain is derived from
    ``TWO_PART_TLDS``, a hand-maintained subset (see its definition). Under a
    suffix missing from it, matching your own site fails, and unrelated sites
    share one registrable domain. Never derive the ``domain`` argument with
    ``extract_domain`` — under such a suffix that yields the public suffix
    itself and matches every site below it. Pass a literal.

    Args:
        url: The URL to check. Must be a valid URL with a scheme and
            network location.
        domain: The domain to match against (e.g., ``'wikipedia.org'``).
            Should not include a scheme or path. Compared case-insensitively,
            ignoring a trailing dot.

    Returns:
        True if the URL's registrable domain matches, False otherwise.
        Returns False for malformed URLs.

    Raises:
        TypeError: If url or domain is not a string. A wrong type is a caller
            error, not a URL that failed to match, so it is surfaced instead
            of being reported as False.
    """
    if not isinstance(domain, str):
        raise TypeError('Domain must be a string.')

    # Trailing dots stripped as extract_domain strips them from the URL,
    # or 'example.com.' never matched.
    domain = _TRAILING_DOTS_AND_SPACE.sub('', domain.strip().lower())

    try:
        url_domain = extract_domain(url, drop_subdomain=True)
    except ValueError:
        logger.debug('Could not extract domain from URL: %r', url)
        return False

    return url_domain == domain
