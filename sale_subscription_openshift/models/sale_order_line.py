# Copyright (C) 2020 Open Source Integrators
# Copyright (C) 2020 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    instance_name = fields.Char("Instance Name")

    def _prepare_subscription_line_data(self):
        """Prepare a dictionnary of values to add lines to a subscription."""
        values = list()
        for line in self:
            if line.product_id.recurring_invoice:
                values.append(
                    (
                        0,
                        False,
                        {
                            "product_id": line.product_id.id,
                            "name": line.name,
                            "quantity": line.product_uom_qty,
                            "uom_id": line.product_uom.id,
                            "price_unit": line.product_id.lst_price,
                            "discount": line.discount
                            if line.order_id.subscription_management != "upsell"
                            else False,
                            "instance_name": line.instance_name,
                        },
                    )
                )
            else:
                values.append(
                    (
                        0,
                        False,
                        {
                            "product_id": line.product_id.id,
                            "name": line.name,
                            "quantity": line.product_uom_qty,
                            "uom_id": line.product_uom.id,
                            "price_unit": line.price_unit,
                            "discount": line.discount
                            if line.order_id.subscription_management != "upsell"
                            else False,
                        },
                    )
                )
        return values
