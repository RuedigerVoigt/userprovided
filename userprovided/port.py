#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Checking Port information for the userprovided library
~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/userprovided
(c) 2020-2021 Rüdiger Voigt
Released under the Apache License 2.0
"""


import logging


def port_in_range(port_number: int) -> bool:
    "Check if the port is within the valid range from 0 to 65536."

    if not isinstance(port_number, int):
        raise ValueError('Port has to be an integer.')

    if 0 < port_number < 65536:
        logging.debug('Port within range')
        return True
    logging.error('Port not within valid range from 0 to 65536')
    return False
