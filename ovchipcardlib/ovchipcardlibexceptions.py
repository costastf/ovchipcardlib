#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
# File: ovchipcardlibexceptions.py
#
"""Exceptions module"""

__author__ = '''Costas Tyfoxylos <costas.tyf@gmail.com>'''
__docformat__ = 'plaintext'
__date__ = '''31-03-2017'''


class UnableToRetrieveToken(Exception):
    """The retrieval of the token failed."""


class UnAuthorized(Exception):
    """Could not verify authorization token."""


class BrokenResponse(Exception):
    """Server did not respond as expected"""
