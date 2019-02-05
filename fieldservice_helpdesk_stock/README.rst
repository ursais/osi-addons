======================
FSM - Helpdesk - Stock
======================

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1| |badge2| 

Odoo Field Service App allows to manage service requests and orders. The app
does not support the logistic side of those activities: Sometimes, the
dispatcher need to ship materials to the field service worker or to the
serviced location.

Odoo Helpdesk App allows to manage support tickets or customer service requests.
The app does not support the logistic side of those activities: Sometimes,
helpdesk users need to ship materials to the customer or to the serviced
location to solve a ticket.

This module allows to integrate material request between a helpdesk ticket and
field service order to be shipped to the customer location or serviced location
and follow up with the Inventory team.

**Table of contents**

.. contents::
   :local:

Usage
=====

* Create a service order with a customer and a ticket
* In Inventory, add products with quantity
* Click on Confirm

    * The delivery order is created
    * The transfer is set on the ticket
    * The state is updated to Confirmed
    * The product, description and quantity requested cannot be changed

* Transfer partially the delivery order

    * The state is updated to Partially Shipped

* Transfer completely the delivery order

    * The state is updated to Done

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/ursais/11.0/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed
`feedback <https://github.com/ursais/11.0/issues/new?body=module:%20fieldservice_helpdesk_stock%0Aversion:%2011.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
~~~~~~~

* Open Source Integrators

Contributors
~~~~~~~~~~~~

* Bhavesh Odedra <bodedra@opensourceintegrators.com>

Other credits
~~~~~~~~~~~~~

The development of this module has been financially supported by:

* Open Source Integrators

Maintainers
~~~~~~~~~~~

.. |maintainer-max3903| image:: https://github.com/max3903.png?size=40px
    :target: https://github.com/max3903
    :alt: max3903
.. |maintainer-bodedra| image:: https://github.com/bodedra.png?size=40px
    :target: https://github.com/bodedra
    :alt: bodedra

|maintainer-max3903| |maintainer-bodedra| 
