# Import Odoo libs
from odoo import api, models


class SaleOrderCancel(models.TransientModel):
    """Inherit cancel sale order wizard to set contact_ids."""

    _inherit = "sale.order.cancel"

    # METHODS #######

    @api.depends("order_id")
    def _compute_recipient_ids(self):
        """Override to include contact_ids in mails for sale orders."""
        super()._compute_recipient_ids()
        for wizard in self:
            if wizard.order_id.contact_ids:
                wizard.recipient_ids = wizard.order_id.contact_ids

    # END #######
