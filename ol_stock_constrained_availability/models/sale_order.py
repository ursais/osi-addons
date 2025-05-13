# Import Odoo Libs
from odoo import fields, models


class SaleOrder(models.Model):
    """Inherit the Object for Method Modification."""

    _inherit = "sale.order"

    # COLUMNS #####

    date_confirm = fields.Datetime(
        string="Confirmation Date",
        readonly=True,
        copy=False,
    )

    # END #########
    # METHODS #####

    def action_confirm(self):
        # Calls the original `action_confirm` method from the super class to
        # confirm the record.
        self.date_confirm = fields.Datetime.now()
        res = super().action_confirm()
        stock_moves = self.picking_ids.move_ids_without_package.filtered(
            lambda l: l.state not in ["done", "cancel"]
        )
        for stock_move in stock_moves:
            if stock_move.product_id.is_constrained:
                stock_move.date = self.date_confirm
        return res

    # END #########
