.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
    :alt: License LGPL-3

========
RMA Sale
========

This module allows you to:

#. Import sales order lines into RMA lines
#. Create a sales order and/or sales order line from one or more RMA lines

Usage
=====

**Import existing sales order lines into an RMA:**

This feature is useful when you create an RMA associated to a product that
was shipped and you have as a reference the customer PO number.

#. Access to a customer RMA.
#. Fill the customer.
#. Press the button *Add from Sales Order*.
#. In the wizard add a sales order and click on *add item* to select the
   lines you want to add to the RMA.

**Create a sales order and/or sales order line from RMA lines:**

#. Go to a approved RMA line.
#. Click on *Create a Sales Quotation*.
#. In the wizard, select an *Existing Quotation to update* or leave it empty
   if you want to create a new one.
#. Fill the quantity to sell in the lines.
#. Hit *Create a Sales Quotation*.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/Eficent/stock-rma/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Jordi Ballester Alomar <jordi.ballester@eficent.com>
* Aaron Henriquez <ahenriquez@eficent.com>
* Lois Rilo <lois.rilo@eficent.com>

Maintainer
----------

This module is maintained by Eficent
