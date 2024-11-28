from odoo import api, models, fields


class SaleOrder(models.Model):
    """
    Adding fields to Sales Order.
    """

    _inherit = "sale.order"

    # COLUMNS ##########

    rush_order = fields.Boolean("Rush Order")

    # END ##########
    # METHODS #########

    @api.onchange(
        "order_line",
        "order_line.product_id",
    )
    def _onchange_rush_order(self):
        self.rush_order = any(
            product_id.triggers_rush
            for product_id in self.mapped("order_line").mapped("product_id")
        )

    # END ##########
