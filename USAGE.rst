=====
Usage
=====

To use ovchipcardlib in a project in an event watching loop you could use the
 following code.

.. code-block:: python

    from ovchipcardlib import Service
    from time import sleep
    from datetime import datetime

    ovchip_username = 'OVCHIP_USERNAME'
    ovchip_password = 'OVCHIP_PASSWORD'
    card_name = 'Mijn OV-Chipkaart'


    service = Service(ovchip_username, ovchip_password)
    card = service.get_card_by_alias(card_name)

    print('Monitoring card with number {}'.format(card.number))
    print('Getting all historic transactions') # here we discard all the old
                                               # ones since we want to monitor
    card.get_latest_transactions()
    print('Got all transactions. Entering the monitoring loop...')
    while True:
        for transaction in card.get_latest_transactions():
            now = datetime.now()
            time_shift = now - transaction.datetime
            delay_message = 'Delay of transaction logging :{}'.format(time_shift)
            body = '\n'.join((str(transaction), delay_message))
            print('Transaction logged at {}'.format(now))
            print(body)
            print(delay_message)
        sleep(60)
