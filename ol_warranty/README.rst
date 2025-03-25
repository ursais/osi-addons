================
Onlogic Warranty
================

Adds warranty expiration date to serial numbers.

=============
Configuration
=============

- On service products there will be a Warranty Period option that can be set for the nubmer of years for warranty
- Set the service product on the attribute value

=====
Usage
=====

When the Delivery order is validated, if a serial number is set on the move line it will look to see if a product with a warranty period is on the variants attribute values.
If there are it will use the longest one it finds and set the warranty expiration date using today's date plus the number of years from the warranty period on the serial record.

Warranty expiration date is also visible on repair orders, related to the serial number.