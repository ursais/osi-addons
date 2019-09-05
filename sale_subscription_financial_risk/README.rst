================================
Sale Subscription Financial Risk
================================

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-ursais%2Fosi--addons-lightgray.png?logo=github
    :target: https://github.com/ursais/osi-addons/tree/12.0/sale_subscription_financial_risk
    :alt: ursais/osi-addons

|badge1| |badge2| |badge3|

The Odoo Subscription module:

* provides different stages for a subscription:
  Draft, In Progress, To Upsell, Closed.
* supports multiples lines of services within a subscription
* Services of a subscription in progress can be modified
  (product, description, quantity, unit price), added or removed.

Some organizations need to be able to suspend a running subscription based on some rules:

* Customer has invoices that are overdue by more than X period of time
  (weeks, months) of the subscription (dynamic credit limit)
* Customer has at least one invoice that is overdue by X days
  (configurable on the customer, by default = 15 days)

This module allows you to define credit and overdue control with dynamic limit based on subscriptions.

**Table of contents**

.. contents::
   :local:

Usage
=====

* Go to Contacts
* Create or select a partner
* Go to the "Financial risk" tab
* Set the credit limit type: "Fixed Amount" or "Based on Subscriptions" and their attributes
* Set the overdue limit

A scheduled action will run everyday to update the subscriptions
(suspend or not) based on the customer credit and overdue statuses.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/ursais/osi-addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed
`feedback <https://github.com/ursais/osi-addons/issues/new?body=module:%20sale_subscription_financial_risk%0Aversion:%2012.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Contributors
------------

* `Amplex Internet <https://www.amplex.net>`_:

  * Jacob Barnard <jbarnard@amplex.net>

* `Open Source Integrators <https://www.opensourceintegrators.com>`_:

  * Maxime Chambreuil <mchambreuil@opensourceintegrators.com>

Maintainers
-----------

This module is maintained by Open Source Integrators.

.. image:: https://github.com/ursais.png
   :target: https://www.opensourceintegrators.com
   :alt: Open Source Integrators

Open Source Integrators™ (OSI) provides customers a unique combination of
open source business process consulting and implementations.

.. |maintainer-max3903| image:: https://github.com/max3903.png?size=40px
    :target: https://github.com/max3903
    :alt: Maxime Chambreuil

Current `maintainer <https://odoo-community.org/page/maintainer-role>`__:

|maintainer-max3903|

This module is part of the `OSI Odoo Addons <https://github.com/ursais/osi-addons/tree/12.0/fieldservice_account_asset>`_ project on GitHub.

You are welcome to contribute. To learn how, please visit https://odoo-community.org/page/Contribute.
