# Copyright (C) 2021, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    substitute_product_ids = fields.Many2many(
        "product.product",
        "bom_optional_product_rel",
        "bom_id",
        "product_id",
        string="Substitute Products",
    )
