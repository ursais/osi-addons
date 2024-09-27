from odoo import models


class ProductConfiguratorSale(models.TransientModel):
    _inherit = "product.configurator.sale"

    def action_config_done(self):
        """Override to add price computation after the order line is created or updated"""
        # Call the original method from the base module
        res = super().action_config_done()

        if self.order_line_id:
            # Update the existing order line
            self.order_line_id._compute_price_unit()  # Explicitly compute the price unit
        else:
            # Create a new order line and compute the price
            new_line = self.env["sale.order.line"].search(
                [("order_id", "=", self.order_id.id)], order="id desc", limit=1
            )
            if new_line:
                new_line._compute_price_unit()  # Compute the price unit for the new line

        return res
