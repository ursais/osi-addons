.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3

================
Helpdesk - Stock
================

Odoo Helpdesk App allows to manage support tickets or customer service requests.
The app does not support the logistic side of those activities: Sometimes,
helpdesk users need to ship materials to the customer or to the serviced
location to solve a ticket.

This module allows the Helpdesk user to request materials to be shipped to the
customer location or serviced location and follow up with the Inventory team.

Usage
=====

* Create a helpdesk ticket with a customer
* In Materials, add products with quantity
* Click on Confirm

  * The delivery order is created
  * The transfer is set on the ticket
  * The state is updated to Confirmed
  * The product, description and quantity requested cannot be changed

* Transfer partially the delivery order

  * The state is updated to Partially Shipped

* Transfer completely the delivery order

  * The state is updated to Done

Credits
=======

* Michael Allen <mallen@opensourceintegrators.com>


Contributors
------------

* Open Source Integrators <http://www.opensourceintegrators.com>
* Brian McMaster <brian@mcmpest.com>
