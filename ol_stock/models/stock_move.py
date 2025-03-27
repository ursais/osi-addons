# Import Odoo libs
from odoo import _, api, models
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    """Inherit stock move to override set location functionality."""

    _inherit = "stock.move"

    # METHODS #####

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            picking_id = vals.get("picking_id")
            if picking_id:
                picking = self.env["stock.picking"].browse(picking_id)
                if picking.picking_type_id.code == "incoming":
                    # Check if the user is in the special group
                    if not self.env.user.has_group(
                        "ol_stock.group_allow_incoming_move_addition"
                    ):
                        raise ValidationError(
                            _(
                                "You are not allowed to add lines to incoming "
                                "transfers. If this is an error, please ask "
                                "your system administrator to add you to the "
                                "'Receipts: Allow Adding Lines to Incoming "
                                "Transfer' security group."
                            )
                        )

        return super().create(vals_list)

    # END #########
