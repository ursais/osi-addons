# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Product(models.Model):
    _inherit = "product.product"

    edi_prod_config_ids = fields.One2many(
        "edi.product.config", "product_id", string="EDI Product Configuration"
    )
