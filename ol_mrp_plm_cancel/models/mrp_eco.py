# Import Odoo libs
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class MrpEco(models.Model):
    """
    Inherit MRP Eco for adding a Cancel Method.
    """

    _inherit = "mrp.eco"

    # COLUMNS ###
    initial_product_state_id = fields.Many2one(
        "product.state",
        string="Initial Product State",
        default=lambda self: self.product_tmpl_id.product_state_id.id,
        help="Shows the state of the product when the ECO was created.",
    )
    current_product_state_id = fields.Many2one(
        "product.state",
        string="Current Product State",
        related="product_tmpl_id.product_state_id",
        help="Shows the current state of the product.",
    )
    # END #######

    @api.onchange("product_tmpl_id")
    def product_tmpl_id_onchange(self):
        """If product changes then update the initial product state."""
        self.initial_product_state_id = self.product_tmpl_id.product_state_id.id

    def action_cancel(self):
        """Similar to final stage functionality, but to cancal an ECO.
        When the cancel button is pressed the ECO will change to the cancel stage
        and reset the product's stage back to it's original.

        ValidationError will show if no stage is set to be a cancel stage."""

        cancel_stage = self.env["mrp.eco.stage"].search(
            [("type_ids", "in", [self.type_id.id]), ("cancel_stage", "=", True)],
            limit=1,
        )
        if cancel_stage:
            self.stage_id = cancel_stage.id
        else:
            raise ValidationError(
                _(
                    "There is no stage set as a Cancel stage. "
                    "Please configure a Cancel stage."
                )
            )
        if self.initial_product_state_id:
            self.product_tmpl_id.product_state_id = self.initial_product_state_id.id

    def write(self, vals):
        """It's possible to move the stage to a cancel stage outside of the cancel button
        so this will ensure the product state gets properly set if this happens."""
        res = super().write(vals)
        if self.stage_id.cancel_stage and self.product_tmpl_id.product_state_id.id:
            self.product_tmpl_id.product_state_id = self.initial_product_state_id.id
        return res
