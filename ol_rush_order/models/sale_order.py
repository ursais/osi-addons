from odoo import api, models, fields


class SaleOrder(models.Model):
    """
    Adding fields to Sales Order.
    """

    _inherit = "sale.order"

    # COLUMNS ##########

    rush_order = fields.Boolean(
        string="Rush Order",
        compute="_compute_rush_order",
        store=True,
        readonly=False,
        tracking=True,
    )
    rush_order_manual = fields.Boolean(
        string="Rush Order Manual Override",
        default=False,
    )

    # END ##########
    # METHODS #########

    @api.depends(
        "order_line.product_id",
        "order_line.product_uom_qty",
        "order_line.product_id.triggers_rush",
        "order_line.product_id.product_template_attribute_value_ids",
        "order_line.product_id.product_template_attribute_value_ids.product_id",
        "order_line.product_id.product_template_attribute_value_ids.product_id.triggers_rush",
    )
    def _compute_rush_order(self):
        for record in self:
            # Filter out lines with qty 0
            valid_lines = record.order_line.filtered(
                lambda line: line.product_uom_qty > 0
            )
            product_ids = valid_lines.mapped("product_id")

            # Compute rush order status
            computed_rush_order = any(
                product.triggers_rush for product in product_ids
            ) or any(
                attr_val.product_id and attr_val.product_id.triggers_rush
                for product in product_ids
                for attr_val in product.product_template_attribute_value_ids
            )

            # If manual override exists and matches computed value, reset the override
            if record.rush_order_manual and computed_rush_order != record.rush_order:
                record.rush_order_manual = False

            # Apply the computed value if not manually overridden
            if not record.rush_order_manual:
                record.rush_order = computed_rush_order

    def write(self, vals):
        if "rush_order" in vals:
            for record in self:
                # Detect a manual change to the rush_order field
                if record.rush_order != vals["rush_order"]:
                    vals["rush_order_manual"] = True

        if "order_line" in vals:
            # Clear manual override when lines are modified
            for record in self:
                record.rush_order_manual = False

        return super().write(vals)

    # END ##########
