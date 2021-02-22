.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3

=======================
Product BOM Cost Rollup
=======================

With Standard Cost Method, products that have bill of materials defined
show rollup cost from the BOM.
This module allows the cost to be rolled up based on BOM's that have
components change standard price.
The module can be used from product template/product variant forms using
"Compute BOM Cost Rollup" or from the Scheduled Job across all BOM's that
need an update.
The module sends an email on modified standard cost products to an email
configured on the Manufacturing App.

=============
Configuration
=============

Go to Manufacturing/ Configuration/ Settings/ BoM Cost Rollup Email
and add email that you want to send BoM cost rollup email to.

Or

Go to Settings/ Users & Companies/ Companies
and add email that you want to send BoM cost rollup email to.

Turn On Debugger mode
Go to Settings/ Technical/ Automation/ Scheduled Actions
Change the interval you want scheduler to run.

=====
Usage
=====

a. Set the BOM Cost Rollup Notification Email
b. To update a single product: Click on the Compute BOM Cost Rollup button
c. To run on BOMs that have changed, run the scheduler manually or in cron mode.


Credits
=======

* Open Source Integrators <http://www.opensourceintegrators.com>

Contributors
============

* Balaji Kannan <bkannan@opensourceintegrators.com>
* Mayank Gosai <mgosai@opensourceintegrators.com>
* Hardik Suthar <hsuthar@opensourceintegrators.com>
