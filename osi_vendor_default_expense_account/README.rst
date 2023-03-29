Overview
========

PQI creates a direct vendor bills for Electric, Utilities. It is hard to 
remember expense account number for vendor bill line.

When we create a vendor bills without any product, Odoo searches for default 
expense account from the list of existing expense account.

This module will resolve issue of remember expense account number. It allows
to set default expense account on contact form.

Usage
=====

- Go to Contacts. Find a service provider vendor. 
- Open that record and edit it. Go to Accounting tab, Turn on 
  "Use Default Expense" field, it will display "Default Expense Account" 
  field where we need to set one expense account. 
- Go to Accounting > Vendors > Bills 
- Create a vendor bill. Select above configured vendor and provide a 
  utilities description. 
- It will automatically picked vendor's default expense account and set it on 
  vendor bill line.

Credits
=======

* Open Source Integrators <http://www.opensourceintegrators.com>

Contributors
============

* Bhavesh Odedra <bodedra@opensourceintegrators.com>
