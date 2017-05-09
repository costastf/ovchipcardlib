=============
ovchipcardlib
=============

A library to interact with the ov-chip card service.

It utilizes the webapi of the mobile apps to get the information.
Very loosely based on https://github.com/OVChip/ovchipapi-python for the
authentication part.

Be aware that the ov-chip card system used in the Netherlands for public
transport was not designed to be real time. So expect a hefty time drift
before the actual checkin/out action and information showing up on the api
and by extension on the transactions list.

Also the sequence of transactions is not guaranteed. It is absolutelly
certain that if there are a lot of checkins/outs closely together they will
appear out of order on the web api. Apparently there is a serverside job that
sorts them once a day.

The library handles that by sorting the list of transactions always. So on
any action it would return a properly ordered list of events but in case of
monitoring through the card.get_latest_transactions() method it is
absolutelly guaranteed that transaction will appear out of order and with a
delay ranging between 2 and 15 minutes according to some simple benchmarks.


* Documentation: http://ovchipcardlib.readthedocs.io/en/latest/

Features
--------

* Can get cards bound with the account and lists of transactions for the cards.
