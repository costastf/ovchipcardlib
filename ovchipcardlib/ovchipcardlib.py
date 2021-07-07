#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: ovchipcardlib.py
#
# Copyright 2017 Costas Tyfoxylos
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to
#  deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.
#

"""
Main code for ovchipcardlib.

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

"""

import logging

import requests

from .helpers import Token, Card
from .ovchipcardlibexceptions import (UnableToRetrieveToken,
                                      UnAuthorized,
                                      BrokenResponse)

__author__ = '''Costas Tyfoxylos <costas.tyf@gmail.com>'''
__docformat__ = '''google'''
__date__ = '''14-04-2017'''
__copyright__ = '''Copyright 2017, Costas Tyfoxylos'''
__credits__ = ["Costas Tyfoxylos"]
__license__ = '''MIT'''
__maintainer__ = '''Costas Tyfoxylos'''
__email__ = '''<costas.tyf@gmail.com>'''
__status__ = '''Development'''  # "Prototype", "Development", "Production".


# This is the main prefix used for logging
LOGGER_BASENAME = '''ovchipcardlib'''
LOGGER = logging.getLogger(LOGGER_BASENAME)
LOGGER.addHandler(logging.NullHandler())


CLIENT_ID = 'nmOIiEJO5khvtLBK9xad3UkkS8Ua'
CLIENT_SECRET = 'FE8ef6bVBiyN0NeyUJ5VOWdelvQa'  # noqa


class Service:  # pylint: disable=too-many-instance-attributes
    """Object representing the ov chip card service.

    Can authenticate with the appropriate credentials and retrieves cards
    from the remote service.
    """

    def __init__(self, username, password):
        """Initializing of the Service object.

        Args:
            username (str): The username to log in with
            password (str): The password to log in with

        """
        logger_name = '{base}.{suffix}'.format(base=LOGGER_BASENAME,
                                               suffix=self.__class__.__name__)
        self._logger = logging.getLogger(logger_name)
        self.username = username
        self.password = password
        self._client_id = CLIENT_ID
        self._client_secret = CLIENT_SECRET
        self._auth_url = 'https://login.ov-chipkaart.nl/oauth2/token'
        self.api_url = 'https://api2.ov-chipkaart.nl/femobilegateway/v1'
        self.locale = 'nl-NL'
        self._cards = []
        self._auth_token = None
        self._token = self._get_token()

    def _get_token(self):
        """Gets the authentication token from the service.

        Returns:
            Token object of the retrieved token

        """
        params = {'username': self.username,
                  'password': self.password,
                  'client_id': self._client_id,
                  'client_secret': self._client_secret,
                  'grant_type': 'password',
                  'scope': 'openid'}
        return self._retrieve_token(params)

    def _refresh_token(self):
        """Refreshes the authentication token from the service.

        Returns:
            True on success

        """
        params = {'refresh_token': self._token.refresh,
                  'client_id': self._client_id,
                  'client_secret': self._client_secret,
                  'grant_type': 'refresh_token'}
        self._token = self._retrieve_token(params)
        return True

    def _retrieve_token(self, data):
        """Does the actual posting to the service for the token.

        Args:
            data (dict): The dictionary with the arguments to post to the
                service

        Returns:
            Token object of the retrieved token

        """
        response = requests.post(self._auth_url, data=data)
        if not response.ok:
            error = response.json().get('error_description', 'Unknown error!')
            raise UnableToRetrieveToken(error)
        token = response.json()
        return Token(token.get('access_token'),
                     token.get('expires_in'),
                     token.get('id_token'),
                     token.get('refresh_token'),
                     token.get('scope'),
                     token.get('token_type'))

    @property
    def authorization_token(self):
        """The authorization token.

        Returns:
             auth_token (str): The string of the authentication token

        """
        if not self._auth_token:
            params = {'authenticationToken': self._token.id}
            url = '{base}/api/authorize'.format(base=self.api_url)
            try:
                response = requests.post(url, data=params)
                data = response.json()
            except ValueError:
                message = ('Status code :{}\n'
                           'Response text :{}'.format(response.status_code,
                                                      response.text))
                raise BrokenResponse(message)
            status_code = data.get('c')
            exception = data.get('e')
            authorization = data.get('o')
            if not status_code == 200:
                raise UnAuthorized(exception or authorization)
            self._auth_token = authorization
        return self._auth_token

    @property
    def cards(self):
        """Retrieves the cards and instantiates the Card objects.

        Returns:
             cards (list): A list of card objects

        """
        if not self._cards:
            params = {'authorizationToken': self.authorization_token,
                      'locale': self.locale}
            url = '{base}/cards/list'.format(base=self.api_url)
            try:
                response = requests.post(url, data=params)
                data = response.json()
            except ValueError:
                # we take for granted that the response went through. This
                # will fail miserably in problematic network conditions where
                #  the response would not actually get through.
                message = ('Status code :{}\n'
                           'Response text :{}'.format(response.status_code,
                                                      response.text))
                raise BrokenResponse(message)
            status_code = data.get('c')
            exception = data.get('e')
            data = data.get('o')
            if not status_code == 200:
                raise LookupError(exception or data)
            self._cards = [Card(self, info) for info in data]
        return self._cards

    def get_card_by_alias(self, alias):
        """Returns a card object by alias.

        Args:
            alias (str):The alias of the card to look for

        Returns:
             A card object if a match found or None

        """
        return next((card for card in self.cards
                     if card.alias.lower() == alias.lower()), None)
