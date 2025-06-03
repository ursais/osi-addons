# Import Odoo libs
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # COLUMNS #####

    payment_preference = fields.Many2one(
        comodel_name="res.paypref",
        string="Payment Preference",
        company_dependent=True,
    )
    net_terms_allowed = fields.Boolean(
        string="Net Terms Allowed",
        compute="_compute_net_terms_allowed",
        store=True,
    )
    net_terms_active = fields.Boolean(string="Front End Net Terms Active")

    # END #########
    # Method #########

    @api.depends("commercial_partner_id.property_payment_term_id")
    def _compute_net_terms_allowed(self):
        """
        Determines whether the partner is allowed to use net terms.
        This is only Used on Frontend eCommerce.
        """
        for partner in self:
            partner.net_terms_allowed = bool(
                partner.commercial_partner_id.property_payment_term_id
            )

    # END #########
