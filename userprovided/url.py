#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
URL related functions of the userprovided library
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
(c) 2020-2021 Rüdiger Voigt
Released under the Apache License 2.0
"""


# python standard library:
import logging
import mimetypes
from typing import Dict, Optional, Union
import urllib.parse

from userprovided import err


def is_url(url: str,
           require_specific_schemes: Union[tuple, None] = None) -> bool:
    """Very basic check if the URL fulfills basic conditions ("LGTM").
       Will not try to connect."""
    parsed = urllib.parse.urlparse(url)

    if parsed.scheme == '':
        logging.debug('The URL has no scheme (like http or https)')
        return False
    if require_specific_schemes:
        if parsed.scheme not in require_specific_schemes:
            logging.error('Scheme %s not supported.', parsed.scheme)
            return False

    if parsed.netloc == '':
        logging.debug('URL is missing or malformed.')
        return False

    return True


def normalize_query_part(query: str,
                         drop_keys: Union[list, tuple, set, None] = None) -> str:
    """Normalize the query part (for example '?foo=1&example=2') of an URL:
       * Remove every chunk that has no value assigned.
       * Sort the remaining chunks alphabetically.
       * Do not change queries without key (old implementations).
        The optional drop_keys allows you to remove specific keys
        (for example trackers)."""
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
            split_chunk = chunk.split('=')
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
    """Normalize an URL:
       * remove whitespace around it,
       * convert scheme and hostname to lowercase,
       * remove ports if they are the standard port for the scheme,
       * remove duplicate slashes from the path,
       * remove fragments (like #foo),
       * remove empty elements of the query part,
       * order the elements in the query part by alphabet,
       The optional drop_keys allows you to remove specific keys
       (for example trackers).

       The option do_not_change_query_part is there, because some content
       management systems use duplicate keys with different values. Sometimes
       that must not raise an exception."""
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
        reassemble.append(normalize_query_part(parsed.query, drop_keys))

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
            logging.error('No hint in URL and mime-type malformed for %s', url)
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
        logging.error(msg)
        return '.unknown'
    elif type_by_url != provided_mime_type:
        # The suggestions contradict each other
        msg = (f"The mime type ({type_by_url}) suggested by the URL ({url}) " +
               "does not match the mime type supplied by the server " +
               f"({provided_mime_type}). Using the extension suggested " +
               "by the URL.")
        logging.error(msg)
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
