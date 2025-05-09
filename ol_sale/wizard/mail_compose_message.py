# Import Odoo libs
from odoo import api, models


class MailComposer(models.TransientModel):
    """Inherit mail compose to adjust partners for sale orders."""

    _inherit = "mail.compose.message"

    # METHODS #######

    @api.depends(
        "composition_mode", "model", "parent_id", "res_domain", "res_ids", "template_id"
    )
    def _compute_partner_ids(self):
        """Override to include contact_ids in mails for sale orders."""
        super()._compute_partner_ids()
        for composer in self:
            if self.model == "sale.order" and composer.res_ids:
                res_ids = composer._evaluate_res_ids()
                order_ids = self.env[composer.model].browse(res_ids)
                if order_ids.contact_ids:
                    composer.partner_ids = order_ids.contact_ids

    # END #######
