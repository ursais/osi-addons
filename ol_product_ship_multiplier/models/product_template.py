# Import Odoo libs
from odoo import api, fields, models


class ProductTemplate(models.Model):
    """

    Adding Fields in Product Template.
    """

    _inherit = "product.template"

    # Method #######
    @api.depends("weight", "carrier_multiplier_id")
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
        comodel_name="delivery.carrier.multiplier",
        string="Inbound Ship Method",
        help="Inbound shipping method to be used for estimating shipping costs.",
    )
    default_shipping_cost = fields.Float(
        string="Cost Multiplier",
        compute="_compute_default_shipping_cost",
        help="Estimated shipping cost. Calculated by multiplying product weight by the inbound shipping method multiplier.",
        store=True,
    )

    # END #######
