# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    standard_price = fields.Float(
        digits="Product Cost Price",
    )


class ProductTemplate(models.Model):
    _inherit = "product.template"

    standard_price = fields.Float(
        digits="Product Cost Price",
    )
