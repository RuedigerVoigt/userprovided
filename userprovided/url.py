#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
URL related functions of the userprovided library
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
Copyright (c) 2020-2025 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""


# python standard library:
import ipaddress
import logging
import mimetypes
from typing import Dict, Optional, Union
import urllib.parse

from userprovided import err


# Known 2-part TLDs (country code second-level domains)
# Note: This is a subset of common 2-part TLDs. For comprehensive coverage,
# consider using the Public Suffix List (https://publicsuffix.org/)
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


def is_url(url: str,
           require_specific_schemes: Union[tuple, None] = None) -> bool:
    """Validates basic URL format without attempting connection.

    Performs basic structural validation of a URL including scheme and
    network location presence. Optionally restricts to specific schemes.

    Args:
        url: The URL string to validate.
        require_specific_schemes: Tuple of allowed schemes (e.g., ('http', 'https')).
            If None, any scheme is allowed. Defaults to None.

    Returns:
        True if URL has valid basic structure, False otherwise.
    """
    parsed = urllib.parse.urlparse(url)

    if parsed.scheme == '':
        logging.debug('The URL has no scheme (like http or https)')
        return False
    if require_specific_schemes:
        if parsed.scheme not in require_specific_schemes:
            logging.debug('Scheme %s not supported.', parsed.scheme)
            return False

    if parsed.netloc == '':
        logging.debug('URL is missing or malformed.')
        return False

    return True


def _normalize_query_part(query: str,
                          drop_keys: Union[list, tuple, set, None] = None) -> str:
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
    keep: Dict[str, str] = dict()
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
                  drop_keys: Union[list, tuple, set, None] = None,
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

    if not parsed.port:
        # There is no port to begin with
        # hostname is lowercase without port
        reassemble.append(parsed.hostname)  # type: ignore[arg-type]
    elif (parsed.scheme in standard_ports and
            parsed.port == standard_ports[parsed.scheme]):
        # There is a port and it equals the standard.
        # That means it is redundant.
        reassemble.append(parsed.hostname)  # type: ignore[arg-type]
    else:
        # There is a port but it is not in the list or not standard
        reassemble.append(f"{parsed.hostname}:{parsed.port}")

    # remove common typo (// in path element):
    reassemble.append(parsed.path.replace('//', '/'))

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


def determine_file_extension(url: str,
                             provided_mime_type: Optional[str] = None) -> str:
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

    extension: Optional[str] = None
    type_by_url: Optional[str] = None
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
            logging.debug('No hint in URL and mime-type malformed for %s', url)
            return '.unknown'
    elif type_by_url is not None and provided_mime_type is None:
        # There is a usable file extension in the URL, but the misconfigured
        # server does not provide a mime type.
        extension = mimetypes.guess_extension(type_by_url)
        # Here no code for extension is None, because mimetypes already
        # guessed a type once we got here and can guess a matching extension.
    elif type_by_url is None and provided_mime_type is None:
        # Neither the URL nor the server does hint to a extension
        msg = (f"Neither URL ({url}) nor mime-type ({provided_mime_type}) " +
               "suggests a file extension.")
        logging.debug(msg)
        return '.unknown'
    elif type_by_url != provided_mime_type:
        # The suggestions contradict each other
        msg = (f"The mime type ({type_by_url}) suggested by the URL ({url}) " +
               "does not match the mime type supplied by the server " +
               f"({provided_mime_type}). Using the extension suggested " +
               "by the URL.")
        logging.debug(msg)
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
        domain = parsed.netloc.lower()

        # Remove 'www.' prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]

        # Known URL shortening service domains
        shortener_domains = {
            'bit.ly', 'bitly.com',
            'tinyurl.com',
            't.co',  # https://help.x.com/en/using-x/url-shortener
            'goo.gl', # EOL 09/2025: https://developers.googleblog.com/en/google-url-shortener-links-will-no-longer-be-available/
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

    Args:
        url: Full URL string (e.g., 'https://www.example.com:8080/path')
        drop_subdomain: If True, extracts only the registrable domain
                        (domain + public suffix), removing subdomains.
                        Handles multi-part TLDs correctly (e.g., .co.uk, .com.au).
                        IP addresses and localhost are returned as-is.

    Returns:
        Domain string without port. For IP addresses (IPv4/IPv6) and localhost,
        returns the address/hostname unchanged.

    Raises:
        ValueError: If url is empty or domain extraction fails

    Example:
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
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")

    try:
        parsed = urllib.parse.urlparse(url.strip())
        domain = parsed.hostname

        if not domain:
            domain = parsed.netloc

        if not domain:
            raise ValueError(f"Could not extract domain from URL: {url}")

        domain = domain.lower().strip()

        if drop_subdomain:
            domain = _extract_registrable_domain(domain, TWO_PART_TLDS)

        return domain

    except AttributeError as e:
        raise ValueError(f"Invalid URL format: {url}") from e


def extract_tld(url: str) -> str:
    """
    Extract the TLD (top-level domain) from a URL.

    Correctly identifies 2-part TLDs (like .co.uk, .com.au) and returns them
    as a single unit. For standard TLDs (like .com, .org), returns just the
    single-part TLD.

    Args:
        url: Full URL string (e.g., 'https://www.example.com/path')

    Returns:
        TLD string with leading dot (e.g., '.com', '.co.uk', '.com.au').
        Returns empty string if TLD cannot be determined (e.g., for IP
        addresses, localhost, or invalid URLs).

    Raises:
        ValueError: If url is empty

    Examples:
        >>> extract_tld('https://www.example.com/path')
        '.com'
        >>> extract_tld('https://example.co.uk')
        '.co.uk'
        >>> extract_tld('https://subdomain.example.com.au/page')
        '.com.au'
        >>> extract_tld('http://192.168.1.1')
        ''
        >>> extract_tld('http://localhost')
        ''
    """
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")

    try:
        parsed = urllib.parse.urlparse(url.strip())
        domain = parsed.hostname

        if not domain:
            domain = parsed.netloc

        if not domain:
            return ''

        domain = domain.lower().strip()

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
        if len(parts) >= 2:
            potential_2part_tld = '.'.join(parts[-2:])
            if potential_2part_tld in TWO_PART_TLDS:
                return '.' + potential_2part_tld

        # Standard single-part TLD
        return '.' + parts[-1]

    except Exception:
        # If parsing fails, return empty string
        return ''


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
        >>> _extract_registrable_domain('192.168.1.1', TWO_PART_TLDS)
        '192.168.1.1'
        >>> _extract_registrable_domain('localhost', TWO_PART_TLDS)
        'localhost'
    """
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
    if len(parts) >= 3:
        potential_2part_tld = '.'.join(parts[-2:])
        if potential_2part_tld in two_part_tlds:
            # Return domain + 2-part TLD
            return '.'.join(parts[-3:])

    # Fall back to simple TLD (e.g., .com, .org)
    # Return last 2 parts (domain + TLD)
    return '.'.join(parts[-2:])