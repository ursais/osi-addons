# Copyright (C) 2024 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class ProductConfiguratorSaleBlanketOrder(models.TransientModel):
    _inherit = "product.configurator.sale.blanket.order"

    def _get_order_line_vals(self, product_id):
        """Add the config session related bom_id to the sale blanket order"""
        vals = super()._get_order_line_vals(product_id=product_id)
        bom = self.env["mrp.bom"].search([("product_id", "=", product_id)], limit=1)
        vals.update(bom_id=bom.id)
        return vals
