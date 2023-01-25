.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

========
Overview
========

This module prevents users from shippings orders that would put customers
above their credit limit based on open invoices.

It adds a new group that allows certain users to manage credit hold of the
customers.

After this module is installed, credit limits will be verified for all
customers.

Configuration
=============

* Add users to the 'Credit Hold' group

Usage
=====

* Sales Hold on Customer: Disallows new sales orders and prevents confirmation
  of existing quotations.

* Credit Hold on Customer: Allows new sales orders, confirmation of orders,
  but prevents orders from being shipped.

* Credit Limit: Maximum allowed receivable balance for a customer.

* Grace period: Time allowed for the customer to make payment after the term 
  has expired.

* Credit Override: When set on sale order, allows shipment on the sale order
  to be processed even if there is a hold on the sale order.

* Credit Override requires special permission to be set on the user.

Credits
=======

Contributors
------------

* OSI Dev Team <contact@opensourceintegrators.com>
* Sandeep Mangukiya <smangukiya@opensourceintegrators.com>
* Maxime Chambreuil <mchambreuil@opensourceintegrators.com>
* Bhavesh Odedra <bodedra@opensourceintegrators.com>
* Balaji Kannan <bkannan@opensourceintegrators.com>
* Hardik Suthar <hsuthar@opensourceintegrators.com>
* Chankya Soni <csoni@opensourceintegrators.com>
