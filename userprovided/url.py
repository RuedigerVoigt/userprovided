#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# python standard library:
import logging
import mimetypes
from typing import Dict, Optional, Union
import urllib.parse


def is_url(url: str,
           require_specific_schemes: Union[tuple, None] = None) -> bool:
    """Very basic check if the URL fulfills basic conditions ("LGTM").
       Will not try to connect."""
    parsed = urllib.parse.urlparse(url)

    if parsed.scheme == '':
        logging.error('The URL has no scheme (like http or https)')
        return False
    if require_specific_schemes:
        if parsed.scheme not in require_specific_schemes:
            logging.error('Scheme %s not supported.', parsed.scheme)
            return False

    if parsed.netloc == '':
        logging.error('URL is missing or malformed.')
        return False

    return True


def normalize_query_part(query: str) -> str:
    """Normalize the query part (for example '?foo=1&example=2') of an URL:
       * remove every chunk that has no value assigned,
       * sort the remaining chunks alphabetically."""
    chunks = query.split('&')
    keep: Dict[str, str] = dict()
    for chunk in chunks:
        if chunk != '':
            split_chunk = chunk.split('=')
            key = split_chunk[0]
            value = split_chunk[1]
            if key != '' and value != '':
                if key in keep:
                    if keep[key] != value:
                        raise ValueError('Duplicate key in URL query with ' +
                                         'conflicting values')
                    else:
                        logging.debug('URL query part contained duplicate ' +
                                      'key but no conflicting value.')
                else:
                    keep[key] = value
    ordered = list()
    if keep:
        for key in sorted(keep):
            ordered.append(f"{key}={keep[key]}")

    return ('&'.join(ordered) if ordered else '')


def normalize_url(url: str) -> str:
    """Normalize an URL:
       * remove whitespace around it,
       * convert scheme and hostname to lowercase,
       * remove ports if they are the standard port for the scheme,
       * remove duplicate slashes from the path,
       * remove fragments (like #foo),
       * remove empty elements of the query part,
       * order the elements in the query part by alphabet,"""
    url = url.strip()

    if not is_url(url):
        raise ValueError('Malformed URL')

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
        print('B')
        # There is a port and it equals the standard.
        # That means it is redundant.
        reassemble.append(parsed.hostname)  # type: ignore[arg-type]
    else:
        print('C')
        # There is a port but it is not in the list or not standard
        reassemble.append(f"{parsed.hostname}:{parsed.port}")
  
    # remove common typo (// in path element):
    reassemble.append(parsed.path.replace('//', '/'))

    # do not change paameters of the path element (!= query)
    reassemble.append(parsed.params)

    reassemble.append(normalize_query_part(parsed.query))

    # urlunparse expects a fifth element (the already removed fragment)
    reassemble.append('')

    url = urllib.parse.urlunparse(reassemble)

    return url


def determine_file_extension(url: str,
                             provided_mime_type: Optional[str] = None) -> str:
    """Guess the correct filename extension from an URL and / or
    the mime-type returned by the server.
    Sometimes a valid URL does not contain a file extension
    (like https://www.example.com/), or it is ambiguous.
    So the mime type acts as a fallback. In case the correct
    extension cannot be determined at all it is set to 'unknown'."""
    if provided_mime_type == '':
        provided_mime_type = None
    type_by_url = mimetypes.guess_type(url)[0]
    if type_by_url is not None and type_by_url == provided_mime_type:
        # Best case: URL and server header suggest the same filetype.
        extension = mimetypes.guess_extension(provided_mime_type)
    elif type_by_url is None and provided_mime_type is not None:
        # The URL does not contain an usable extension, but
        # the server provides one.
        extension = mimetypes.guess_extension(provided_mime_type)
    elif type_by_url is not None and provided_mime_type is None:
        # Misconfigured server but the type can be guessed.
        extension = mimetypes.guess_extension(type_by_url)
    else:
        # Worst case: neither the URL nor the server does hint to the
        # correct extension
        logging.error("The mime type (%s) suggested by the URL (%s)" +
                      "does not match the mime type supplied" +
                      "by the server (%s).",
                      (type_by_url, url, provided_mime_type))
        extension = None

    if extension is not None:
        if extension == '.bat' and provided_mime_type == 'text/plain':
            # text/plain is mapped to .bat in python 3.6.
            # Python 3.8 correctly guesses .txt as extension.
            return '.txt'

        if extension == '.htm':
            return '.html'

        return extension
    else:
        return '.unknown'
