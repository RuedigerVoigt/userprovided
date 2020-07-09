#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# python standard library:
import logging
import mimetypes
from typing import Optional, Union
from urllib.parse import urlparse


def is_url(url: str,
           require_specific_schemes: Union[tuple, None] = None) -> bool:
    u"""Very basic check if the URL fulfills basic conditions
        ("LGTM"). Will not try to connect."""
    parsed = urlparse(url)

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


def determine_file_extension(url: str,
                             provided_mime_type: Optional[str] = None) -> str:
    u"""Guess the correct filename extension from an URL and / or
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
