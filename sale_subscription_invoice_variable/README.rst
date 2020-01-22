.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3

===============================
Subscription Variable Invoicing
===============================

Include variable consumed amount in recurring bills.

The Subscription must have an Analytic Account, and
the additional consumptions should be recorded as Analytic Lines.

When the recurring invoice is being generated,
we look for the amounts in Analytic Lines
matching the Analytic Accountand the dates of the invoicing period.

These will be added to the generated invoice.


Usage
=====

* On the Subscription, ensure the Analytic Account is set.
* Add the amaount to invoice as Analytic Lines.
* Generated the next recurring invoice.


Credits
=======

* Daniel Reis <dreis@opensourceintegrators.com>


Contributors
------------

* Open Source Integrators <https://www.opensourceintegrators.com>
