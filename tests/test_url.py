#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for the url module of userprovided.
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
Released under the Apache License 2.0
"""

# ruff: noqa

from unittest.mock import patch

from hypothesis import given, assume, strategies as st
import pytest

import userprovided


def test_is_url():
    # missing scheme:
    assert userprovided.url.is_url('noscheme.example.com') is False
    # wrong scheme:
    assert userprovided.url.is_url('ftp://example.com', ('http', 'https')) is False
    # scheme with typo (one instead of two slashes):
    assert userprovided.url.is_url('https:/example.com') is False
    # valid URLs:
    assert userprovided.url.is_url('https://example.com') is True
    assert userprovided.url.is_url('https://example.com', ('https', 'http')) is True
    assert userprovided.url.is_url('https://example.com', ('https')) is True
    assert userprovided.url.is_url('https://subdomain.example.com') is True
    assert userprovided.url.is_url('https://example.com/index.php?id=42') is True
    # A plain string is treated as a single scheme name, not matched as
    # a substring: ('https') is a string, not a tuple, and 'http' in 'https'
    # is True — this must not let http URLs pass an https-only check.
    assert userprovided.url.is_url('http://example.com', ('https')) is False
    assert userprovided.url.is_url('http://example.com', 'https') is False
    assert userprovided.url.is_url('https://example.com', 'https') is True


def test_is_url_non_string():
    # Non-string input is a caller error and raises TypeError, not a leaky
    # error from len() and not a silent False.
    with pytest.raises(TypeError):
        userprovided.url.is_url(None)
    with pytest.raises(TypeError):
        userprovided.url.is_url(123)
    # is_shortened_url calls is_url first, so it propagates the same contract.
    with pytest.raises(TypeError):
        userprovided.url.is_shortened_url(None)


def test_url_length_limits():
    long_url = 'https://example.com/' + 'a' * 2048
    # is_url rejects over-long URLs
    assert userprovided.url.is_url(long_url) is False
    # normalize_url raises ValueError (calls is_url internally)
    with pytest.raises(ValueError):
        userprovided.url.normalize_url(long_url)
    # extract_domain raises ValueError
    with pytest.raises(ValueError):
        userprovided.url.extract_domain(long_url)
    # extract_tld raises ValueError
    with pytest.raises(ValueError):
        userprovided.url.extract_tld(long_url)
    # ip functions return False / None for over-long URLs
    assert userprovided.ip.is_loopback(long_url) is False
    assert userprovided.ip.is_private(long_url) is False
    assert userprovided.ip.is_link_local(long_url) is False
    assert userprovided.ip.is_potential_ssrf_target(long_url) is False


def test_normalize_query_part():
    # By mistake a full URL is provided instead of only the query part:
    with pytest.raises(ValueError):
        userprovided.url._normalize_query_part('https://www.example.com/index.php?foo=foo&foo=bar')
    # Duplicate key in query part of URL query with conflicting values:
    with pytest.raises(userprovided.err.QueryKeyConflict):
        userprovided.url._normalize_query_part('foo=foo&foo=bar')
    # Duplicate key in query part of URL with the same value:
    assert userprovided.url._normalize_query_part('foo=bar&foo=bar') == 'foo=bar'
    # Chunk of query is malformed: the = is missing:
    assert userprovided.url._normalize_query_part('missingequalsign&foo=bar') == 'foo=bar'
    assert userprovided.url._normalize_query_part('foo=bar&missingequalsign&') == 'foo=bar'
    # Drop specific key (with tuple, list and set):
    assert userprovided.url._normalize_query_part('foo=1&bar=2&', drop_keys=('bar')) == 'foo=1'
    assert userprovided.url._normalize_query_part('foo=1&bar=2&', drop_keys=['bar']) == 'foo=1'
    assert userprovided.url._normalize_query_part('foo=1&bar=2&', drop_keys={'bar'}) == 'foo=1'
    # Try to drop non-existent key:
    assert userprovided.url._normalize_query_part('foo=1&bar=2&', drop_keys=['not_in_url']) == 'bar=2&foo=1'
    # drop_key is set, but empty or None:
    assert userprovided.url._normalize_query_part('foo=1&bar=2&', drop_keys=[]) == 'bar=2&foo=1'
    assert userprovided.url._normalize_query_part('foo=1&bar=2&', drop_keys=None) == 'bar=2&foo=1'
    # Multiple = signs in parameter values (preserve full value):
    assert userprovided.url._normalize_query_part('token=eyJuYW1lIjoiSm9obiJ9==') == 'token=eyJuYW1lIjoiSm9obiJ9=='
    assert userprovided.url._normalize_query_part('redirect=https://site.com?param=value') == 'redirect=https://site.com?param=value'
    assert userprovided.url._normalize_query_part('formula=x=2*y+3') == 'formula=x=2*y+3'
    assert userprovided.url._normalize_query_part('token=abc=def&name=john') == 'name=john&token=abc=def'
    # All params dropped: keep is empty, returns empty string
    assert userprovided.url._normalize_query_part('foo=1', drop_keys=['foo']) == ''


@pytest.mark.parametrize("test_url,normalized_url", [
    # remove whitespace around the URL:
    (' https://www.example.com/ ', 'https://www.example.com/'),
    # Convert scheme and hostname to lowercase
    ('HTTPS://www.ExAmPlE.com', 'https://www.example.com'),
    # Remove standard port for scheme (http)
    ('http://www.example.com:80', 'http://www.example.com'),
    # Remove standard port for scheme (https)
    ('https://www.example.com:443', 'https://www.example.com'),
    # Keep non-standard port for scheme (http)
    ('https://www.example.com:123', 'https://www.example.com:123'),
    # Remove duplicate slashes from the path (1)
    ('https://www.example.com//index.html',
     'https://www.example.com/index.html'),
    # Remove duplicate slashes from the path (2)
    ('https://www.example.com/en//index.html',
     'https://www.example.com/en/index.html'),
    # remove fragment when query is not present
    (' https://www.example.com/index.html#test ',
     'https://www.example.com/index.html'),
    # remove fragment when query is present
    (' https://www.example.com/index.php?name=foo#test ',
     'https://www.example.com/index.php?name=foo'),
    # remove fragment when path is not present
    (' https://www.example.com/#test ', 'https://www.example.com/'),
    # Ignore empty query
    ('https://www.example.com/index.php?',
     'https://www.example.com/index.php'),
    # remove empty elements of the query part
    ('https://www.example.com/index.php?name=foo&example=',
     'https://www.example.com/index.php?name=foo'),
    # order the elements in the query part by alphabet
    ('https://www.example.com/index.py?c=3&a=1&b=2',
     'https://www.example.com/index.py?a=1&b=2&c=3'),
    # URL with non standard query part (does not follow key=value syntax).
    # Mentioned in RFC 3986 as "erroneous" because it mixes query and path.
    # However still used by some software.
    ('https://www.example.com/forums/forumdisplay.php?example-forum',
     'https://www.example.com/forums/forumdisplay.php?example-forum'),
    # Empty query, but '?' indicating one
    ('https://www.example.com/index.php?', 'https://www.example.com/index.php'),
    # IPv6 host: keep the square brackets (urlparse strips them on parsing)
    ('http://[::1]/', 'http://[::1]/'),
    # IPv6 host: lowercase the hex digits
    ('https://[2001:DB8::1]/path', 'https://[2001:db8::1]/path'),
    # IPv6 host: remove standard port for scheme (http)
    ('http://[::1]:80/', 'http://[::1]/'),
    # IPv6 host: remove standard port for scheme (https)
    ('https://[2001:db8::1]:443/index.html', 'https://[2001:db8::1]/index.html'),
    # IPv6 host: keep non-standard port
    ('http://[::1]:8080/path', 'http://[::1]:8080/path'),
    # IPv6 host: query part is still normalized
    ('https://[2001:db8::1]/index.py?c=3&a=1&b=2',
     'https://[2001:db8::1]/index.py?a=1&b=2&c=3'),
    # Userinfo is dropped by design (username and password)
    ('https://user:pass@www.example.com/', 'https://www.example.com/'),
    # Userinfo is dropped by design (username only)
    ('https://user@www.example.com/', 'https://www.example.com/'),
    # Userinfo dropped while host, port and query are still normalized
    ('http://user:pass@www.Example.com:8080/p?b=2&a=1',
     'http://www.example.com:8080/p?a=1&b=2'),
    # Userinfo dropped for an IPv6 host
    ('http://user:pass@[::1]:8080/', 'http://[::1]:8080/')
])
def test_normalize_url(test_url, normalized_url):
    assert userprovided.url.normalize_url(test_url) == normalized_url


def test_normalize_url_exceptions():
    # input is not an URL
    with pytest.raises(ValueError):
        userprovided.url.normalize_url('somestring')
    # Contradiction: drop keys, but query part shall be unchanged
    with pytest.raises(userprovided.err.ContradictoryParameters):
        userprovided.url.normalize_url(
            'https://www.example.com/index.php?id=1',
            ['id'],
            do_not_change_query_part = True)


def test_normalize_url_removing_keys():
    # The function just hands over drop_keys to normalize_query_part, so
    # more cases are tested in test_normalize_query_part() above and this
    # just ensures the parameter is passed on.
    assert userprovided.url.normalize_url(
        'https://www.example.com/index.py?c=3&a=1&b=2',
        drop_keys=['c']) == 'https://www.example.com/index.py?a=1&b=2'


def test_normalize_url_unchanged_query():
    assert userprovided.url.normalize_url(
        '  https://www.example.com/index.php?foo=1&foo=2',
        [],
        do_not_change_query_part = True
    ) == 'https://www.example.com/index.php?foo=1&foo=2'


def test_determine_file_extension():
    # URL hint matches server header
    assert userprovided.url.determine_file_extension('https://www.example.com/example.pdf', 'application/pdf') == '.pdf'
    # URL does not provide a hint, but the HTTP header does
    assert userprovided.url.determine_file_extension('https://www.example.com/', 'text/html') == '.html'
    # URL hint and HTTP header contradict each other!
    # Fallback to suffix suggested by URL:
    assert userprovided.url.determine_file_extension('https://www.example.com/example.pdf', 'text/html') == '.pdf'
    # no server header, but hint in URL
    assert userprovided.url.determine_file_extension('https://www.example.com/example.pdf', '') == '.pdf'
    # no hint at all
    assert userprovided.url.determine_file_extension('https://www.example.com/', '') == '.unknown'
    # malformed server header and no hint in the URL
    assert userprovided.url.determine_file_extension('https://www.example.com/', 'malformed/nonexist') == '.unknown'
    # unknown extension in URL and no mime-type by server
    assert userprovided.url.determine_file_extension('https://www.example.com/index.foo', None) == '.unknown'
    # text/plain
    assert userprovided.url.determine_file_extension('https://www.example.com/test.txt', 'text/plain') == '.txt'
    # .htm -> html
    assert userprovided.url.determine_file_extension('https://www.example.com/test.htm', 'text/plain') == '.html'
    assert userprovided.url.determine_file_extension('https://www.example.com/test.htm', 'doesnotmatter') == '.html'


def test_is_shortened_url():
    # Test known shortening services
    assert userprovided.url.is_shortened_url('https://bit.ly/abc123') is True
    assert userprovided.url.is_shortened_url('https://tinyurl.com/xyz789') is True
    assert userprovided.url.is_shortened_url('https://t.co/abcdef') is True
    assert userprovided.url.is_shortened_url('https://goo.gl/maps123') is True
    assert userprovided.url.is_shortened_url('https://lnkd.in/xyz') is True

    # Test with www prefix
    assert userprovided.url.is_shortened_url('https://www.bit.ly/abc123') is True
    assert userprovided.url.is_shortened_url('https://www.tinyurl.com/xyz789') is True

    # Test case insensitivity
    assert userprovided.url.is_shortened_url('https://BIT.LY/abc123') is True
    assert userprovided.url.is_shortened_url('https://TINYURL.COM/xyz789') is True

    # Test non-shortened URLs
    assert userprovided.url.is_shortened_url('https://example.com/page') is False
    assert userprovided.url.is_shortened_url('https://google.com/search') is False
    assert userprovided.url.is_shortened_url('https://github.com/user/repo') is False

    # Test invalid URLs
    assert userprovided.url.is_shortened_url('not-a-url') is False
    assert userprovided.url.is_shortened_url('') is False
    assert userprovided.url.is_shortened_url('ftp://bit.ly/test') is True  # Valid URL with shortener domain

    # Test edge cases
    assert userprovided.url.is_shortened_url('https://bit.ly') is True  # No path
    assert userprovided.url.is_shortened_url('http://tinyurl.com/') is True  # HTTP

    # Test some enterprise/business shorteners
    assert userprovided.url.is_shortened_url('https://rebrand.ly/custom') is True
    assert userprovided.url.is_shortened_url('https://short.link/test') is True
    assert userprovided.url.is_shortened_url('https://cutt.ly/example') is True


def test_is_shortened_url_exception_handling():
    # Test exception handling in is_shortened_url when urlparse throws unexpected error
    # Need to patch where it's used in the url module
    with patch('userprovided.url.urllib.parse.urlparse') as mock_parse:
        # Make is_url succeed but then fail in is_shortened_url
        mock_parse.side_effect = [
            # First call, inside is_url. Needs every attribute is_url reads,
            # including the port it validates.
            type('obj', (object,), {'scheme': 'https', 'netloc': 'bit.ly',
                                    'port': None})(),
            Exception('Unexpected error')  # Second call in is_shortened_url
        ]
        # Should return False and not raise
        assert userprovided.url.is_shortened_url('https://bit.ly/test') is False


# There are some edge cases in which `mimetypes.guess_extension`
# (in the python standard library) has different return values
# depending on the Python version used.
def test_determine_file_extension_version_inconsistencies():
    with patch('mimetypes.guess_extension', return_value='.bat'):
        assert userprovided.url.determine_file_extension('https://www.example.com/test.txt', 'text/plain') == '.txt'
    with patch('mimetypes.guess_extension', return_value='.htm'):
        assert userprovided.url.determine_file_extension('https://www.example.com/test.htm', 'text/plain') == '.html'
    with patch('mimetypes.guess_extension', return_value=None):
        assert userprovided.url.determine_file_extension('https://www.example.com/test.htm', 'text/plain') == '.unknown'


@pytest.mark.parametrize("test_url,expected_domain", [
    # Basic domain extraction without port
    ('https://www.example.com/path', 'www.example.com'),
    ('https://example.com', 'example.com'),
    ('http://subdomain.example.com/page', 'subdomain.example.com'),
    # Domain extraction with port
    ('https://www.example.com:8080/path', 'www.example.com'),
    ('http://example.com:3000', 'example.com'),
    # Domain extraction with query parameters and fragments
    ('https://www.example.com/path?foo=bar', 'www.example.com'),
    ('https://example.com#fragment', 'example.com'),
    ('https://www.example.com/path?foo=bar#fragment', 'www.example.com'),
    # IP addresses
    ('http://192.168.1.1/path', '192.168.1.1'),
    ('http://192.168.1.1:8080', '192.168.1.1'),
    ('http://[2001:db8::1]/path', '2001:db8::1'),
    # Localhost
    ('http://localhost/path', 'localhost'),
    ('http://localhost:3000', 'localhost'),
    # Case normalization
    ('https://WWW.EXAMPLE.COM', 'www.example.com'),
    ('HTTPS://Example.Com/Path', 'example.com'),
])
def test_extract_domain_basic(test_url, expected_domain):
    assert userprovided.url.extract_domain(test_url) == expected_domain


@pytest.mark.parametrize("test_url,expected_domain", [
    # Simple TLDs - subdomains should be removed
    ('https://www.example.com/path', 'example.com'),
    ('https://subdomain.example.com', 'example.com'),
    ('https://deep.subdomain.example.com', 'example.com'),
    # 2-part TLDs - should preserve domain + 2-part TLD
    ('https://www.example.co.uk/page', 'example.co.uk'),
    ('https://subdomain.example.co.uk', 'example.co.uk'),
    ('https://deep.sub.example.co.uk', 'example.co.uk'),
    ('https://www.example.com.au/page', 'example.com.au'),
    ('https://subdomain.example.com.au', 'example.com.au'),
    ('https://www.example.co.jp', 'example.co.jp'),
    ('https://www.example.gov.uk', 'example.gov.uk'),
    ('https://www.example.com.br', 'example.com.br'),
    ('https://www.example.co.in', 'example.co.in'),
    # Already registrable domains
    ('https://example.com', 'example.com'),
    ('https://example.co.uk', 'example.co.uk'),
    # IP addresses - should be returned unchanged
    ('http://192.168.1.1:8080/path', '192.168.1.1'),
    ('http://10.0.0.1', '10.0.0.1'),
    ('http://[2001:db8::1]/path', '2001:db8::1'),
    ('http://[::1]', '::1'),
    # Localhost and single-word domains
    ('http://localhost:3000', 'localhost'),
    ('http://intranet/page', 'intranet'),
])
def test_extract_domain_drop_subdomain(test_url, expected_domain):
    assert userprovided.url.extract_domain(test_url, drop_subdomain=True) == expected_domain


def test_extract_domain_errors():
    # Empty URL
    with pytest.raises(ValueError, match="URL cannot be empty"):
        userprovided.url.extract_domain('')

    with pytest.raises(ValueError, match="URL cannot be empty"):
        userprovided.url.extract_domain('   ')

    # Invalid URL format - missing scheme
    with pytest.raises(ValueError, match="Could not extract domain"):
        userprovided.url.extract_domain('not-a-url')

    # Invalid URL format - scheme only
    with pytest.raises(ValueError, match="Could not extract domain"):
        userprovided.url.extract_domain('http://')


def test_extract_domain_edge_cases():
    # URL with authentication info
    result = userprovided.url.extract_domain('https://user:pass@example.com/path')
    assert result == 'example.com'

    # URL with authentication info and drop_subdomain
    result = userprovided.url.extract_domain('https://user:pass@www.example.co.uk', drop_subdomain=True)
    assert result == 'example.co.uk'

    # Very deep subdomain hierarchy
    result = userprovided.url.extract_domain('https://a.b.c.d.e.f.example.com', drop_subdomain=True)
    assert result == 'example.com'

    # Very deep subdomain with 2-part TLD
    result = userprovided.url.extract_domain('https://a.b.c.d.e.f.example.co.uk', drop_subdomain=True)
    assert result == 'example.co.uk'


def test_extract_domain_whitespace():
    # URL with leading/trailing whitespace
    assert userprovided.url.extract_domain('  https://example.com  ') == 'example.com'
    assert userprovided.url.extract_domain('\thttps://example.com\n') == 'example.com'


def test_extract_domain_ipv6_variations():
    # Various IPv6 formats (urlparse returns them as-is, doesn't compress)
    assert userprovided.url.extract_domain('http://[::1]:8080') == '::1'
    assert userprovided.url.extract_domain('http://[fe80::1]') == 'fe80::1'
    assert userprovided.url.extract_domain('http://[2001:0db8:0000:0000:0000:0000:0000:0001]') == '2001:0db8:0000:0000:0000:0000:0000:0001'

    # IPv6 with drop_subdomain should return unchanged
    assert userprovided.url.extract_domain('http://[::1]', drop_subdomain=True) == '::1'
    assert userprovided.url.extract_domain('http://[2001:db8::1]', drop_subdomain=True) == '2001:db8::1'


@pytest.mark.parametrize("test_url,expected_tld", [
    # Standard single-part TLDs
    ('https://www.example.com/path', '.com'),
    ('https://example.org', '.org'),
    ('https://subdomain.example.net/page', '.net'),
    ('https://example.edu', '.edu'),
    ('https://example.gov', '.gov'),
    # 2-part TLDs
    ('https://www.example.co.uk/page', '.co.uk'),
    ('https://subdomain.example.com.au', '.com.au'),
    ('https://example.co.jp', '.co.jp'),
    ('https://www.example.gov.uk', '.gov.uk'),
    ('https://example.com.br', '.com.br'),
    ('https://example.co.in', '.co.in'),
    ('https://example.co.nz', '.co.nz'),
    ('https://example.co.za', '.co.za'),
    # With ports and paths
    ('https://example.com:8080/path', '.com'),
    ('https://www.example.co.uk:443/page?foo=bar', '.co.uk'),
    # Case insensitivity
    ('https://EXAMPLE.COM', '.com'),
    ('https://Example.CO.UK', '.co.uk'),
])
def test_extract_tld_basic(test_url, expected_tld):
    assert userprovided.url.extract_tld(test_url) == expected_tld


def test_extract_tld_edge_cases():
    # IP addresses should return empty string
    assert userprovided.url.extract_tld('http://192.168.1.1') == ''
    assert userprovided.url.extract_tld('http://192.168.1.1:8080/path') == ''
    assert userprovided.url.extract_tld('http://[::1]') == ''
    assert userprovided.url.extract_tld('http://[2001:db8::1]/path') == ''

    # Localhost and single-word domains should return empty string
    assert userprovided.url.extract_tld('http://localhost') == ''
    assert userprovided.url.extract_tld('http://localhost:3000') == ''
    assert userprovided.url.extract_tld('http://intranet/page') == ''

    # Invalid URLs should return empty string (not raise)
    assert userprovided.url.extract_tld('not-a-url') == ''


def test_extract_tld_errors():
    # Empty URL should raise ValueError
    with pytest.raises(ValueError, match="URL cannot be empty"):
        userprovided.url.extract_tld('')

    with pytest.raises(ValueError, match="URL cannot be empty"):
        userprovided.url.extract_tld('   ')


def test_extract_tld_whitespace():
    # Whitespace should be handled
    assert userprovided.url.extract_tld('  https://example.com  ') == '.com'
    assert userprovided.url.extract_tld('\thttps://example.co.uk\n') == '.co.uk'


@pytest.mark.parametrize("url,domain,expected", [
    # Exact match:
    ('https://example.com/page', 'example.com', True),
    ('https://wikipedia.org/wiki/Test', 'wikipedia.org', True),
    # Subdomain match (www):
    ('https://www.example.com/page', 'example.com', True),
    ('https://www.wikipedia.org/wiki', 'wikipedia.org', True),
    # Subdomain match (other):
    ('https://en.wikipedia.org/wiki', 'wikipedia.org', True),
    ('https://deep.sub.example.com/page', 'example.com', True),
    # 2-part TLDs:
    ('https://www.example.co.uk/page', 'example.co.uk', True),
    ('https://sub.example.com.au', 'example.com.au', True),
    # Case insensitivity:
    ('https://WWW.EXAMPLE.COM', 'example.com', True),
    ('https://example.com', 'EXAMPLE.COM', True),
    # Domain with whitespace:
    ('https://example.com', '  example.com  ', True),
    # Non-matching domains:
    ('https://example.com/page', 'other.com', False),
    ('https://evil.com', 'wikipedia.org', False),
    # Subdomain that looks similar but different registrable domain:
    ('https://example.com.evil.com', 'example.com', False),
    # Malformed URLs:
    ('not-a-url', 'example.com', False),
    ('', 'example.com', False),
    # IP addresses don't match domain names:
    ('http://192.168.1.1', 'example.com', False),
])
def test_url_matches_domain(url, domain, expected):
    assert userprovided.url.url_matches_domain(url, domain) is expected


def test_extract_domain_unparseable():
    """urllib rejects an unclosed IPv6 literal -- no mock needed."""
    with pytest.raises(ValueError, match="Invalid URL format"):
        userprovided.url.extract_domain('http://[::1')


def test_extract_tld_unparseable():
    """Same input as above, but this function reports it with an empty string."""
    assert userprovided.url.extract_tld('http://[::1') == ''


def test_extract_tld_unexpected_error_propagates():
    """An unexpected error must reach the caller, not be masked as 'no TLD'.

    Only a parse failure is reported with an empty string; anything else is a
    bug and would previously have been swallowed by a broad except Exception.
    """
    with patch('userprovided.url.urllib.parse.urlparse',
               side_effect=RuntimeError('mocked')):
        with pytest.raises(RuntimeError):
            userprovided.url.extract_tld('https://example.com')


def test_host_from_url_exception():
    """Cover the Exception handler in _host_from_url (url.py)."""
    with patch('userprovided.url.urllib.parse.urlparse',
               side_effect=RuntimeError('mocked')):
        assert userprovided.url._host_from_url('https://example.com') is None


@pytest.mark.parametrize("host,expected", [
    # lowercasing and trailing root-label dots:
    ('Example.COM.', 'example.com'),
    ('example.com..', 'example.com'),
    ('  example.com  ', 'example.com'),
    # IDNA: unicode, punycode, and upper-case unicode spellings converge:
    ('münchen.example', 'xn--mnchen-3ya.example'),
    ('xn--mnchen-3ya.example', 'xn--mnchen-3ya.example'),
    ('MÜNCHEN.example', 'xn--mnchen-3ya.example'),
    # IPv6 equivalence — bracketed, unbracketed, expanded, upper-case:
    ('::1', '::1'),
    ('0:0:0:0:0:0:0:1', '::1'),
    ('[::1]', '::1'),
    ('[0:0:0:0:0:0:0:1]', '::1'),
    ('2001:DB8::1', '2001:db8::1'),
    # IPv4 unchanged:
    ('192.168.1.1', '192.168.1.1'),
    # ASCII hostnames pass through — normalizer, not validator:
    ('localhost', 'localhost'),
])
def test_normalize_hostname(host, expected):
    assert userprovided.url.normalize_hostname(host) == expected


@pytest.mark.parametrize("not_a_string", [None, 123, b'example.com'])
def test_normalize_hostname_type_error(not_a_string):
    with pytest.raises(TypeError):
        userprovided.url.normalize_hostname(not_a_string)


@pytest.mark.parametrize("empty_host", ['', '   ', '.', '[]'])
def test_normalize_hostname_value_error(empty_host):
    with pytest.raises(ValueError):
        userprovided.url.normalize_hostname(empty_host)


def test_normalize_hostname_rejects_overlong_input():
    with pytest.raises(ValueError):
        userprovided.url.normalize_hostname('a' * 2049)


def test_normalize_hostname_idna_fallback():
    # An empty label makes the IDNA codec raise UnicodeError
    # ("label empty") => best-effort fallback to the lowercased
    # unicode form instead of raising.
    assert userprovided.url.normalize_hostname('Ä..b') == 'ä..b'


@given(host=st.text(max_size=100))
def test_normalize_hostname_idempotent(host):
    try:
        normalized = userprovided.url.normalize_hostname(host)
    except ValueError:
        assume(False)
    assert userprovided.url.normalize_hostname(normalized) == normalized


@pytest.mark.parametrize("host,drop_subdomain,expected", [
    ('www.example.co.uk', True, 'example.co.uk'),
    ('deep.sub.example.com', True, 'example.com'),
    # normalization applies before the registrable domain is extracted:
    ('www.MÜNCHEN.example.', True, 'xn--mnchen-3ya.example'),
    # without drop_subdomain only the normalization happens:
    ('www.example.co.uk', False, 'www.example.co.uk'),
    # IP literals returned canonicalized regardless of drop_subdomain:
    ('192.168.1.1', True, '192.168.1.1'),
    ('[::1]', True, '::1'),
    ('[::1]', False, '::1'),
    # single-word hosts:
    ('localhost', True, 'localhost'),
    ('localhost', False, 'localhost'),
])
def test_extract_domain_from_host(host, drop_subdomain, expected):
    assert userprovided.url.extract_domain_from_host(
        host, drop_subdomain=drop_subdomain) == expected


def test_extract_domain_from_host_propagates_errors():
    with pytest.raises(TypeError):
        userprovided.url.extract_domain_from_host(None)
    with pytest.raises(ValueError):
        userprovided.url.extract_domain_from_host('')


def test_url_functions_reject_non_string():
    # A wrong type is a caller error: these used to leak an AttributeError
    # from .strip() instead of following the library's TypeError contract.
    for wrong_type in (None, 123, ['https://example.com']):
        with pytest.raises(TypeError):
            userprovided.url.extract_domain(wrong_type)
        with pytest.raises(TypeError):
            userprovided.url.extract_tld(wrong_type)
        # url_matches_domain checks both of its parameters:
        with pytest.raises(TypeError):
            userprovided.url.url_matches_domain(
                'https://example.com', wrong_type)
        with pytest.raises(TypeError):
            userprovided.url.url_matches_domain(wrong_type, 'example.com')


def test_is_url_malformed_does_not_raise():
    # urllib.parse raises for an unclosed IPv6 literal. A validator must
    # classify such input as invalid instead of raising at the caller.
    assert userprovided.url.is_url('http://[::1') is False
    assert userprovided.url.is_url('http://[') is False


@pytest.mark.parametrize('malformed', [
    'http://[::1',              # urlparse fails outright
    'https://[::1]:notaport',   # parses, but the port is invalid
    'https://example.com:99999',  # port out of range
])
def test_normalize_url_uses_its_own_message(malformed):
    # urllib's messages quote the offending value; this one must not.
    with pytest.raises(ValueError, match='Malformed URL'):
        userprovided.url.normalize_url(malformed)


@pytest.mark.parametrize('url, expected', [
    ('https://bit.ly/x', True),
    # netloc carries the port and the userinfo, hostname does not:
    ('https://bit.ly:443/x', True),
    ('https://evil.com@bit.ly/x', True),
    ('https://www.bit.ly/x', True),
    # not a shortener, even though the userinfo names one:
    ('https://bit.ly@example.com/x', False),
    ('https://example.com/x', False),
])
def test_is_shortened_url_ignores_userinfo_and_port(url, expected):
    assert userprovided.url.is_shortened_url(url) is expected


@pytest.mark.parametrize('url', [
    'http://user:pass@',   # netloc is 'user:pass@', hostname is None
    'http://@',
    'http://:8080',
])
def test_extract_domain_never_returns_netloc(url):
    # Falling back to netloc handed the caller credentials or a bare port
    # as if they were a domain.
    with pytest.raises(ValueError):
        userprovided.url.extract_domain(url)
    assert userprovided.url.extract_tld(url) == ''


@pytest.mark.parametrize('test_url, expected', [
    ('https://example.com//a', 'https://example.com/a'),
    ('https://example.com///a', 'https://example.com/a'),
    ('https://example.com////a', 'https://example.com/a'),
    ('https://example.com/en///index.html', 'https://example.com/en/index.html'),
    ('https://example.com/a//b///c', 'https://example.com/a/b/c'),
    # a single slash is untouched:
    ('https://example.com/a/b', 'https://example.com/a/b'),
])
def test_normalize_url_collapses_slash_runs(test_url, expected):
    # str.replace consumes non-overlapping matches, so one pass left a
    # duplicate behind for three or more slashes.
    assert userprovided.url.normalize_url(test_url) == expected


@pytest.mark.parametrize('test_url', [
    'https://example.com///a',
    'https://example.com/a//b///c',
    'https://example.com/en///index.html',
])
def test_normalize_url_is_idempotent(test_url):
    # The output is an identity key, so normalizing an already normalized URL
    # must not produce a second, different key.
    once = userprovided.url.normalize_url(test_url)
    assert userprovided.url.normalize_url(once) == once


def test_normalize_url_equivalent_spellings_share_one_key():
    # The point of normalizing: URLs for the same resource collapse to one key.
    variants = ['https://example.com/a',
                'https://example.com//a',
                'https://example.com///a',
                'https://example.com////a']
    keys = {userprovided.url.normalize_url(v) for v in variants}
    assert keys == {'https://example.com/a'}


@pytest.mark.parametrize('test_url', [
    'https://example.com:notaport',
    'https://example.com:99999',      # above 65535
    'https://example.com:-1',
    'https://[::1]:notaport',
])
def test_is_url_rejects_invalid_port(test_url):
    # urlparse does not validate the port, it raises on attribute access.
    # A URL no client could dial must not be reported as valid.
    assert userprovided.url.is_url(test_url) is False


@pytest.mark.parametrize('test_url', [
    'https://example.com:443',
    'https://example.com:8080',
    'https://example.com:0',          # 0 is in range
    'https://example.com:65535',      # the highest valid port
    'https://example.com',            # no port at all
])
def test_is_url_accepts_valid_port(test_url):
    assert userprovided.url.is_url(test_url) is True


def test_log_records_escape_control_characters(caplog):
    """User input must reach the log as repr(), so it cannot forge log lines.

    A raw %s would put the newline into the record and let an attacker append
    a line that looks like it came from the application itself.
    """
    import logging
    forged = 'https://example.com/\nERROR:root:transfer approved'
    with caplog.at_level(logging.DEBUG, logger='root'):
        userprovided.ip.is_potential_ssrf_target('http://127.0.0.1/')
        userprovided.url.url_matches_domain(forged, 'example.com')
    for record in caplog.records:
        assert '\n' not in record.getMessage()
