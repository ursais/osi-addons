# Import Odoo libs
from odoo import api, fields, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    """

    Adding Fields in Product Template.
    """

    _inherit = "product.template"

    # COLUMNS ###

    carrier_multiplier_id = fields.Many2one(
        "delivery.carrier.multiplier",
        string="Inbound Ship Method",
        company_dependent=True,
        check_company=True,
    )
    default_shipping_cost = fields.Float(
        string="Cost Multiplier",
        compute="_compute_default_shipping_cost",
    )

    # END #######

    # Methods #######

    @api.depends(
        "weight",
        "carrier_multiplier_id",
        "carrier_multiplier_id.multiplier",
    )
    @api.depends_context("company")
    def _compute_default_shipping_cost(self):
        for rec in self:
            default_shipping_cost = 0.0
            if rec.carrier_multiplier_id:
                default_shipping_cost = (
                    rec.weight * rec.carrier_multiplier_id.multiplier
                )
            rec.default_shipping_cost = default_shipping_cost

    # END #######
