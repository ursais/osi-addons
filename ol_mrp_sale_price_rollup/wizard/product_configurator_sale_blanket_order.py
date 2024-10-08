from odoo import models


class ProductConfiguratorSaleBlanketOrder(models.TransientModel):
    _inherit = "product.configurator.sale.blanket.order"

    def action_config_done(self):
        """Override to add price computation after the order line is created or updated"""
        # Call the original method from the base module
        res = super().action_config_done()

        if self.order_line_id:
            # Update the existing order line
            self.order_line_id.onchange_product()  # Explicitly compute the price unit
        else:
            # Create a new order line and compute the price
            new_line = self.env["sale.blanket.order.line"].search(
                [("order_id", "=", self.order_id.id)], order="id desc", limit=1
            )
            if new_line:
                # Commit line so we can trigger onchange to finalize price
                self.env.cr.commit()
                new_line.onchange_product()  # Compute the price unit for the new line

        return res
