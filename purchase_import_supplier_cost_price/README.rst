.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

==========================
Update Supplier Cost Price
==========================

This module will update the supplier cost prices from a spreadsheet.

It will work on following conditions:

* If the Internal Reference does not exist, the line is skipped and it will not create any new product.
* If the Cost Price is empty in the file, the line is skipped.
* If the supplier was not supplying this product before, then the information is added in Odoo with the default values.
        
Usage
=====

#. Create CSV file with following two columns:

   * Internal Reference
   * Cost Price

#. Go to Purchase and click on "Update Supplier Cost Prices"
#. Select XXX as the Supplier and the CSV file to upload
#. Click on "Update"
#. Check that supplier cost prices of XXX products are updated according to the data in the file.

Credits
=======

Contributors
------------

* Bhavesh Odedra <bodedra@opensourceintegrators.com>
