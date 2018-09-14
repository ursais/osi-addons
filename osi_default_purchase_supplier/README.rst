.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=========================
Default Purchase Supplier
=========================

This module will restrict to confirm PO/SO if holds generic products.

Usage
=====

* Go to Purchases > Purchase > Requests for Quotation
* Create a new one.
* Generic supplier will be auto fill up.
* If logged user has purchase users access rights then supplier field will be
  readonly and hide print/confirm button will. No restriction for manager to
  change supplier field.
* Confirm the order, will restrict if order lines have generic products and
  send email to purchase order creator for action.
* Go to Sales > Orders > Quotations
* Create a new one.
* Confirm the order, will restrict if order lines have generic products.

Credits
=======

* Bhavesh Odedra <bodedra@opensourceintegrators.com>

Contributors
------------

* Open Source Integrators <http://www.opensourceintegrators.com>
