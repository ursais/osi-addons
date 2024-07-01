# Import Odoo libs
from odoo import _, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    """
    Add new fields to product templates
    """

    _inherit = "sale.order"

    # COLUMNS #####
    original_request_date = fields.Date(string="Original Customer Requested Date")
    original_commitment_date = fields.Datetime(
        string="Original Shipment Commitment Date"
    )
    # END #########

    # METHODS #########

    def action_confirm(self):
        """
        Inherit method for set up value for original_request_date and original_commitment_date
        """
        res = super().action_confirm()
        self.original_commitment_date = (
            self.commitment_date or self.expected_date
        )
        if not self.original_request_date:
            raise ValidationError(
                _("Original Customer Requested Date is required to confirm the order.")
            )
        return res

    # END #########
