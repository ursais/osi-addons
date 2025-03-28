# Import Odoo libs
from odoo import api, models


class StockPicking(models.Model):
    """Inherit stock Picking to unreserve on creation if operation type is set to."""

    _inherit = "stock.picking"

    # METHODS #####

    def action_confirm(self):
        # Call the original button_validate method to confirm the picking
        res = super().action_confirm()

        # After the picking is confirmed, check if unreserve_on_create is enabled
        for picking in self:
            if (
                picking.picking_type_id.code == "incoming"
                and picking.picking_type_id.unreserve_on_create
            ):
                # Unreserve stock moves for incoming shipments
                picking.do_unreserve()

        return res

    # END #########
