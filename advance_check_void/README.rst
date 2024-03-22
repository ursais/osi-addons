.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

========
Overview
========

This module is used to make vendor bill payments via checks and also void the checks. 
With this module we can keep a track of payment check History and also see all voided Checks.

Configuration
=============
Install OSI Advance Check Void Module

Usage
=====

To use this module

* Applicable to payments that are type Check only
* Go to Accounting > Vendors > Payments
* Go to the payment that has payment type Check and Check is printed
* There are two options of Void
* Void: Voids check only and allows to reprint check
* Void Check and Payment: Reverses payment on date specified, Opens bills, Reconciles AP and Bank accounts and log void details
* The payment is now in Void status for Audit purposes

Credits
=======

* Murtada Karjikar  <mkarjikar@opensourceintegrators.com>

Authors
=======

* Open Source Integrators <contact@opensourceintegrators.com>

Contributors
============

* Murtada Karjikar <mkarjikar@opensourceintegrators.com>
* Patrick Wilson <pwilson@opensourceintegrators.com>

History
=======

14.0.1.0.0
----------
- Migration from v13 to v14
 
13.0.1.0.2
----------
- Did changes in .xml files according to odoo version 13.
- Added the search view in payment.check.history object.
- Done some code optimization.

13.0.1.0.1
----------
- Solved error in print_checks method 
- Removed empty Keys in manifest.py file...

13.0.1.0.0
----------
- Payment Check History Menuitem is added into Account_accountant module under Accounting Main Menu.
- Inherited account.payment object to add checks void functionality.
- is_visible_check boolean field is added to make check_number visible.
- is_readonly_check boolean field is added to make check_number readonly.
- Void state is added to account.payment object.
- onchange_payment_method new method is added in account.payment object, to make visible check_number field on condition.
- print_checks overrided this method.
- unmark_sent overrided this method added to Void the checks.
- void_check_reversal_payment new method is written to Void Check and Payment.
- payment.check.history new object created to keep a record of all payments done by checks.
- payment.check.void new object created to keep a record of all voided checks to see the voided checks, added button Void Checks on account.payment .
- Button Print Checks is used to have the report of particular check.
