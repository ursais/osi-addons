from odoo import api, models, fields


class SaleOrder(models.Model):
    """
    Adding fields to Sales Order.
    """

    _inherit = "sale.order"

    # COLUMNS ##########

    rush_order = fields.Boolean(
        "Rush Order",
        compute="_compute_rush_order",
        store=True,
        readonly=False,
    )

    # END ##########
    # METHODS #########

    @api.depends(
        "order_line.product_id",
        "order_line.product_id.triggers_rush",
        "order_line.product_id.product_template_attribute_value_ids",
        "order_line.product_id.product_template_attribute_value_ids.product_id",
        "order_line.product_id.product_template_attribute_value_ids.product_id.triggers_rush",
    )
    def _compute_rush_order(self):
        for record in self:
            product_ids = record.mapped("order_line").mapped("product_id")
            if not record.rush_order:
                record.rush_order = any(
                    product.triggers_rush for product in product_ids
                ) or any(
                    attr_val.product_id and attr_val.product_id.triggers_rush
                    for product in product_ids
                    for attr_val in product.product_template_attribute_value_ids
                )

    # END ##########
