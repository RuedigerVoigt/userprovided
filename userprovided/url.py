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
import re
import urllib.parse

from userprovided import err


# Practical upper bound for URL length. No hard RFC limit exists, but most
# HTTP servers and browsers reject URLs beyond 2048–8192 characters.
# Accepting arbitrarily long strings risks slow regex processing and memory use.
_MAX_URL_LENGTH = 2048

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


def _host_from_url(url: str) -> str | None:
    """Extract the lowercase hostname from a URL, or None on failure.

    Raises:
        TypeError: If url is not a string. A non-string is a caller error,
            not a URL that failed to parse, so it is surfaced rather than
            swallowed into a None return.
    """
    if not isinstance(url, str):
        raise TypeError('URL must be a string.')
    if len(url) > _MAX_URL_LENGTH:
        return None
    try:
        host = urllib.parse.urlparse(url.strip()).hostname
        return host.lower() if host else None
    except Exception:
        return None


def is_url(url: str,
           require_specific_schemes: tuple | str | None = None) -> bool:
    """Validates basic URL format without attempting connection.

    Performs basic structural validation of a URL including scheme and
    network location presence. Optionally restricts to specific schemes.

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
        logging.debug('URL exceeds maximum length of %d characters.', _MAX_URL_LENGTH)
        return False

    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        # urllib raises for malformed input like an unclosed IPv6 literal
        # ('http://[::1'). Classifying a URL as invalid is what this function
        # is for, so return False instead of raising at the caller.
        logging.debug('URL could not be parsed.')
        return False

    if parsed.scheme == '':
        logging.debug('The URL has no scheme (like http or https)')
        return False
    if require_specific_schemes:
        if isinstance(require_specific_schemes, str):
            # A bare string would be checked with substring matching:
            # 'http' in 'https' is True, so ('https') — a string, not a
            # tuple — would accept http URLs. Treat it as one scheme name.
            require_specific_schemes = (require_specific_schemes,)
        if parsed.scheme not in require_specific_schemes:
            logging.debug('Scheme %r not supported.', parsed.scheme)
            return False

    if parsed.netloc == '':
        logging.debug('URL is missing or malformed.')
        return False

    try:
        # urllib validates the port lazily, on attribute access. Without this
        # a URL no client could ever dial ('https://example.com:notaport',
        # or a port above 65535) would be reported as valid.
        parsed.port
    except ValueError:
        logging.debug('URL has an invalid port.')
        return False

    return True


def _normalize_query_part(query: str,
                          drop_keys: list | tuple | set | None = None) -> str:
    """Normalizes URL query parameters for consistent formatting.

    Processes query parameters by removing empty values, sorting alphabetically,
    and optionally filtering out specified keys. Preserves legacy query formats
    that don't follow key=value syntax.

    Args:
        query: Query string to normalize (without leading '?').
        drop_keys: Collection of parameter keys to remove from the query.
            Can be list, tuple, or set. Defaults to None.

    Returns:
        Normalized query string with parameters sorted alphabetically.

    Raises:
        ValueError: If a full URL is provided instead of just the query part.
        QueryKeyConflict: If duplicate keys have conflicting values.
    """
    if is_url(query):
        raise ValueError('Provide only the query part to normalize_query_part')

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
                    logging.debug(
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
                  drop_keys: list | tuple | set | None = None,
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
            Can be list, tuple, or set. Defaults to None.
        do_not_change_query_part: If True, preserves original query format
            to avoid issues with legacy systems using duplicate keys.
            Defaults to False.

    Returns:
        Normalized URL string with consistent formatting.

    Raises:
        ValueError: If the URL is malformed.
        ContradictoryParameters: If both drop_keys and do_not_change_query_part
            are specified.
    """
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
    if host and ':' in host:
        # urlparse strips the square brackets from IPv6 literals.
        # Restore them, otherwise the reassembled URL is invalid.
        host = f"[{host}]"

    if not port:
        # There is no port to begin with
        # hostname is lowercase without port
        reassemble.append(host)  # type: ignore[arg-type]
    elif (parsed.scheme in standard_ports and
            port == standard_ports[parsed.scheme]):
        # There is a port and it equals the standard.
        # That means it is redundant.
        reassemble.append(host)  # type: ignore[arg-type]
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
      no brackets.
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

    candidate = host.strip().lower().rstrip('.')

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

    if not candidate.isascii():
        try:
            return candidate.encode('idna').decode('ascii')
        except UnicodeError:
            logging.debug(
                'Hostname could not be IDNA-encoded. '
                'Returning the lowercased unicode form.')

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


def determine_file_extension(url: str,
                             provided_mime_type: str | None = None) -> str:
    """Determines appropriate file extension from URL and/or MIME type.

    Attempts to guess the correct file extension by analyzing the URL path
    and optionally using a provided MIME type as fallback. Handles cases
    where URLs lack extensions or have ambiguous formats.

    Args:
        url: The URL to analyze for file extension hints.
        provided_mime_type: MIME type from server response headers.
            Used as fallback when URL doesn't provide clear extension.
            Defaults to None.

    Returns:
        File extension with leading dot (e.g., '.pdf', '.html') or
        '.unknown' if extension cannot be determined.
    """
    if provided_mime_type:
        provided_mime_type = provided_mime_type.strip()
    if provided_mime_type == '':
        provided_mime_type = None

    extension: str | None = None
    type_by_url: str | None = None
    parsed_url = urllib.parse.urlparse(url)
    if parsed_url.path not in ('', '/'):
        type_by_url = mimetypes.guess_type(parsed_url.path)[0]

    if type_by_url is not None and type_by_url == provided_mime_type:
        # Best case: URL and server header suggest the same filetype.
        extension = mimetypes.guess_extension(provided_mime_type)
    elif type_by_url is None and provided_mime_type is not None:
        # The URL does not contain an usable extension, but
        # the server provides a mime type.
        extension = mimetypes.guess_extension(provided_mime_type)
        if extension is None:
            logging.debug('No hint in URL and mime-type malformed for %r', url)
            return '.unknown'
    elif type_by_url is not None and provided_mime_type is None:
        # There is a usable file extension in the URL, but the misconfigured
        # server does not provide a mime type.
        extension = mimetypes.guess_extension(type_by_url)
        # Here no code for extension is None, because mimetypes already
        # guessed a type once we got here and can guess a matching extension.
    elif type_by_url is None and provided_mime_type is None:
        # Neither the URL nor the server does hint to a extension
        logging.debug('Neither URL %r nor mime-type %r suggests a '
                      'file extension.', url, provided_mime_type)
        return '.unknown'
    elif type_by_url != provided_mime_type:  # pragma: no branch
        # The suggestions contradict each other
        logging.debug('The mime type %r suggested by the URL %r does not '
                      'match the mime type supplied by the server (%r). '
                      'Using the extension suggested by the URL.',
                      type_by_url, url, provided_mime_type)
        extension = mimetypes.guess_extension(type_by_url)  # type: ignore[arg-type]

    # Handle errors and irregularities in mimetypes:
    if extension == '.bat' and provided_mime_type == 'text/plain':
        # text/plain is mapped to .bat in python 3.6.
        # Python 3.8 correctly guesses .txt as extension.
        return '.txt'

    if extension == '.htm':
        return '.html'

    if extension is None:
        return '.unknown'

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
        logging.debug('Invalid URL provided to shortened URL check')
        return False

    try:
        parsed = urllib.parse.urlparse(url)
        # hostname, not netloc: netloc carries the userinfo and the port, so
        # 'https://evil.com@bit.ly/' and 'https://bit.ly:443/' would both slip
        # past the lookup.
        domain = (parsed.hostname or '').lower()

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
        logging.debug('Error parsing URL for shortened URL detection')
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
        ValueError: If url is empty or domain extraction fails

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
        domain = urllib.parse.urlparse(url.strip()).hostname
    except ValueError as e:
        # urllib rejects malformed input such as an unclosed IPv6 literal.
        raise ValueError("Invalid URL format.") from e

    if not domain:
        # netloc is deliberately not used as a fallback: it carries the
        # userinfo and the port, so 'http://user:pass@' would be handed back
        # as if it were a domain.
        raise ValueError("Could not extract domain from URL.")

    domain = domain.lower().strip()

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
        domain = urllib.parse.urlparse(url.strip()).hostname
    except ValueError:
        # Same failure as in extract_domain, but this function reports "no TLD
        # could be determined" with an empty string instead of raising.
        return ''

    if not domain:
        # netloc is deliberately not used as a fallback -- see extract_domain.
        return ''

    # rstrip: a trailing root-label dot ('example.com.') is legal in a fully
    # qualified name and would otherwise be counted as an empty final label,
    # making every such host report '.' as its TLD.
    domain = domain.lower().strip().rstrip('.')

    if not domain:
        # The host consisted of dots only.
        return ''

    # Check if it's an IP address (IPv4 or IPv6)
    try:
        ipaddress.ip_address(domain)
        # It's an IP address, no TLD
        return ''
    except ValueError:
        # Not an IP address, continue
        pass

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

    # Check if the domain is an IP address (IPv4 or IPv6)
    try:
        ipaddress.ip_address(domain)
        # It's a valid IP address, return as-is
        return domain
    except ValueError:
        # Not an IP address, continue with normal processing
        pass

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
            Should not include a scheme or path. Compared case-insensitively.

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

    domain = domain.strip().lower()

    try:
        url_domain = extract_domain(url, drop_subdomain=True)
    except ValueError:
        logging.debug('Could not extract domain from URL: %r', url)
        return False

    return url_domain == domain
