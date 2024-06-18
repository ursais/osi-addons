# Import Odoo libs
from odoo import api, models, _
from odoo.exceptions import ValidationError


class MRPEco(models.Model):
    """
    Inherit MRP Eco for Method Overriding.
    """
    _inherit = "mrp.eco"

    initial_product_state_id = fields.Many2one(
        comodel_name="product.state",
        string="Product State"
    )

    def action_cancel(self):
        cancel_stage = self.env['mrp.eco.stage'].search([('type_ids', 'in', [self.type_id]), ('cancel_stage', '=', True)])
        if cancel_stage:
            self.stage_id = cancel_stage.id
        else:
            raise ValidationError(
                    _(
                        "There is no stage set as a ‘Cancel’ stage. Please configure a ‘Cancel’ stage."
                    )
                )
