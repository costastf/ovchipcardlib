#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
# File: helpers.py
"""Helper Modules"""

import requests
import logging
from collections import namedtuple
from ovchipcardlibexceptions import BrokenResponse
from datetime import datetime
from time import sleep

__author__ = '''Costas Tyfoxylos <costas.tyf@gmail.com>'''
__docformat__ = 'plaintext'
__date__ = '''31-03-2017'''

# This is the main prefix used for logging
LOGGER_BASENAME = '''ovchipcardhelpers'''
LOGGER = logging.getLogger(LOGGER_BASENAME)
LOGGER.addHandler(logging.NullHandler())


Token = namedtuple('Token', ('access',
                             'expires_in',
                             'id',
                             'refresh',
                             'scope',
                             'type'))


class Card(object):
    """Model of the card object"""

    def __init__(self, service_instance, data):
        logger_name = '{base}.{suffix}'.format(base=LOGGER_BASENAME,
                                               suffix=self.__class__.__name__)
        self._logger = logging.getLogger(logger_name)
        self._service = service_instance
        self._data = data
        self._transactions = []
        self._latest_transactions = []

    @property
    def alias(self):
        return self._data.get('alias')

    @property
    def auto_reloading(self):
        return self._data.get('autoReloadEnabled')

    @property
    def balance(self):
        return float(self._data.get('balance')) / 100

    @property
    def balance_datetime(self):
        return self.timestamp_to_datetime(self._data.get('balanceDate'))

    @property
    def expiry_datetime(self):
        return self.timestamp_to_datetime(self._data.get('expiryDate'))

    @staticmethod
    def timestamp_to_datetime(timestamp):
        return datetime.fromtimestamp(float(timestamp / 1000))

    @property
    def default(self):
        return self._data.get('defaultCard')

    @property
    def number(self):
        return self._data.get('mediumId')

    @property
    def status(self):
        return self._data.get('status')

    @property
    def status_announcement(self):
        return self._data.get('statusAnnouncement')

    @property
    def type(self):
        return self._data.get('type')

    def get_latest_transactions(self):
        """Gets the latest transactions

        Returns transactions happening after the last time this was called
        and clears itself upon conclusion. Can be used to monitor the live
        transactions on the card.

        :return: A list of transaction objects.
        """
        _ = self.transactions  # noqa
        transactions = self._latest_transactions[:]
        self._latest_transactions = []
        return transactions

    @property
    def transactions(self):
        """Presents the transactions of the card

        :return: A list of transaction objects.
        """
        if not self._transactions:
            for transactions in self._get_transactions_by_window():
                self._transactions.extend(transactions)
                self._latest_transactions.extend(transactions)
        else:
            found = 0
            try:
                for transactions in self._get_transactions_by_window():
                    for transaction in transactions:
                        exists = next((trip for trip in self._transactions
                                       if trip.datetime == transaction.datetime
                                       ), None)
                        if exists:
                            found += 1
                            message = ('Transaction already '
                                       'exists {}').format(transaction)
                            self._logger.debug(message)
                            if found == 10:
                                self._logger.debug('Matched already 10 existing'
                                                   ' transactions, breaking...')
                                raise StopIteration
                        else:
                            self._transactions.append(transaction)
                            self._latest_transactions.append(transaction)
                            message = 'Added transaction {}'.format(transaction)
                            self._logger.debug(message)
                    # added a slight delay on retrieving from the api so it
                    # is not overwhelmed
                    sleep(0.5)
            except StopIteration:
                pass
        self._transactions.sort(key=lambda x: x.datetime, reverse=True)
        return self._transactions

    def _get_transactions_by_window(self):
        window = 20
        data = {}
        params = {'authorizationToken': self._service.authorization_token,
                  'mediumId': self.number,
                  'offset': 0,
                  'locale': self._service.locale}
        while not window > data.get('totalSize', 20):
            status_code, _, data = self._get_transaction_response(params)
            params['offset'] = int(data.get('nextOffset'))
            transactions = [Transaction(record)
                            for record in data.get('records')]
            yield transactions
        status_code, _, data = self._get_transaction_response(params)
        params['offset'] = int(data.get('nextOffset'))
        transactions = [Transaction(record)
                        for record in data.get('records')]
        yield transactions

    def _get_transaction_response(self, params):
        url = '{base}/transaction/list'.format(base=self._service.api_url)
        response = requests.post(url, data=params)
        try:
            data = response.json()
        except ValueError:
            message = 'Server Error. Response {}'.format(response.text)  #
            self._logger.debug(message)
            raise BrokenResponse(message)
        status_code = data.get('c')
        exception = data.get('e')
        data = data.get('o')
        if not status_code == 200:
            raise LookupError(exception or data)
        return status_code, exception, data


class Transaction(object):
    def __init__(self, data):
        self._data = data
        self.timestamp_to_datetime = Card.timestamp_to_datetime

    def __str__(self):
        """String representation of the Transaction object"""
        text = ('Transaction type :{}'.format(self.name),
                'Starting point   :{}'.format(self.check_in_info),
                'Station          :{}'.format(self.station),
                'Price            :{}'.format(self.fare),
                'Date             :{}'.format(self.datetime),
                'Company Used     :{}'.format(self.company))
        return '\n'.join(text)

    @property
    def check_in_info(self):
        return self._data.get('checkInInfo')

    @property
    def check_in_text(self):
        return self._data.get('checkInText')

    @property
    def e_purse_mut(self):
        return self._data.get('ePurseMut')

    @property
    def e_purse_mut_info(self):
        return self._data.get('ePurseMutInfo')

    @property
    def fare(self):
        return self._data.get('fare')

    @property
    def fare_calculation(self):
        return self._data.get('fareCalculation')

    @property
    def fare_text(self):
        return self._data.get('fareText')

    @property
    def type(self):
        return self._data.get('modalType')

    @property
    def product_info(self):
        return self._data.get('productInfo')

    @property
    def company(self):
        return self._data.get('pto')

    @property
    def product_text(self):
        return self._data.get('productText')

    @property
    def datetime(self):
        return self.timestamp_to_datetime(self._data.get('transactionDateTime'))

    @property
    def explanation(self):
        return self._data.get('transactionExplanation')

    @property
    def station(self):
        return self._data.get('transactionInfo')

    @property
    def name(self):
        return self._data.get('transactionName')

    @property
    def priority(self):
        return self._data.get('transactionPriority')
