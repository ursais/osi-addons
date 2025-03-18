# Module ol_fraud_detection

The Fraud Detection module uses the [MaxMind minfraud API](https://dev.maxmind.com/minfraud/) to
check the Risk Score of a customer-placed order. For example, via Click-to-Buy, eCommerce orders, etc.
If the Risk Score is above a certain threshold, a hold is placed on the order.

This module uses the `minfraud` packed available on PiPy.
 
- [Developer Docs](https://minfraud.readthedocs.io/en/latest/#)
- [Python Source Code](https://github.com/maxmind/minfraud-api-python) 

## Set Up

The Fraud Detection module must call out to the MaxMind API. Therefore, it needs the following
System Parameters entered into Odoo after install:

- ol_fraud_detection.maxmind_key
