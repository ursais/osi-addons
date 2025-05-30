# Import Odoo libs
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # COLUMNS #####

    payment_preference = fields.Many2one(
        comodel_name="res.paypref",
        string="Payment Preference",
        company_dependent=True,
    )
    net_terms_allowed = fields.Boolean(compute="_compute_net_terms_allowed")
    net_terms_active = fields.Boolean(string="Frontend Net Terms Active")

    # END #########
    # Method #########

    def _compute_net_terms_allowed(self):
        """Enable the partner is allowed to the net terms; This is only Used on Frontend eCommerce."""
        for partner in self:
            net_terms_allowed = False
            if partner.commercial_partner_id.property_payment_term_id:
                net_terms_allowed = True
            partner.net_terms_allowed = net_terms_allowed

    # END #########