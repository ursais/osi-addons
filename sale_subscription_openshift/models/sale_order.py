# Copyright (C) 2020 Open Source Integrators
# Copyright (C) 2020 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _cart_update(
        self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs
    ):
        lines = super(SaleOrder, self)._cart_update(
            product_id, line_id, add_qty, set_qty, **kwargs
        )
        sale_line = self.env["sale.order.line"].browse(lines.get("line_id"))
        if sale_line.product_id.recurring_invoice:
            sale_line.price_unit = 0
            if kwargs.get("instance_name"):
                sale_line.instance_name = kwargs.get("instance_name")
        return lines
