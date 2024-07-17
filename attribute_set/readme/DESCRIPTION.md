This module allows the user to create Attributes to any model. This is a
basic module in the way that **it does not provide views to display
these new Attributes.**

Each Attribute created will be related to an **existing field** (in case
of a *"native"* Attribute) or to a newly **created field** (in case of a
*"custom"* Attribute).

A *"custom"* Attribute can be of any type : Char, Text, Boolean, Date,
Binary... but also Many2one or Many2many.

In case of m2o or m2m, these attributes can be related to **custom
options** created for the Attribute, or to **existing Odoo objects**
from other models.

Last but not least an Attribute can be **serialized** using the Odoo SA
module
[base_sparse_field](https://github.com/odoo/odoo/tree/16.0/addons/base_sparse_field)
. It means that all the serialized attributes will be stored in a single
"JSON serialization field" and will not create new columns in the
database (and better, it will not create new SQL tables in case of
Many2many Attributes), **increasing significantly the requests speed**
when dealing with thousands of Attributes.
