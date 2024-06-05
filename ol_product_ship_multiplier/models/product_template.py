# Import Odoo libs
from odoo import fields, models


class ProductTemplate(models.Model):
    """

    Adding Fields in Product Template.
    """

    _inherit = "product.template"

    # Method #######
    def _compute_default_shipping_cost(self):
        for rec in self:
            default_shipping_cost = 1
            if rec.carrier_multiplier_id:
                default_shipping_cost = (
                    rec.weight * rec.carrier_multiplier_id.multiplier
                )
            rec.default_shipping_cost = default_shipping_cost

    # END #######

    # COLUMNS ###

    carrier_multiplier_id = fields.Many2one(
        comodel_name="delivery.carrier.multiplier", string="Inbound Ship Method"
    )
    default_shipping_cost = fields.Float(
        string="Cost Multiplier", compute="_compute_default_shipping_cost"
    )

    # END #######
