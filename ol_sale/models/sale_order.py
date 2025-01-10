# Import Odoo libs
from odoo import _, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    """
    Add new fields to Sale Order
    """

    _inherit = "sale.order"

    # COLUMNS #####
    original_request_date = fields.Date(
        string="Original Customer Requested Date",
        copy=False,
    )
    original_commitment_date = fields.Datetime(
        string="Original Shipment Commitment Date",
        copy=False,
    )
    account_manager_id = fields.Many2one(
        "res.users",
        related="partner_id.account_manager_id",
        string="Account Manager",
        store=True,
    )
    end_user = fields.Many2one("res.partner")
    integrator = fields.Many2one("res.partner")
    delivery_note = fields.Text(string="Delivery Note")
    mrp_note = fields.Text(string="MRP Note")

    # END #########

    # METHODS #########

    def action_confirm(self):
        """
        Inherit method for set up value for original_request_date and original_commitment_date
        """
        res = super().action_confirm()
        for rec in self:
            rec.original_commitment_date = self.commitment_date or self.expected_date
            if not rec.original_request_date:
                raise ValidationError(
                    _(
                        "Original Customer Requested Date is required to confirm the order."
                    )
                )
        return res

    # END #########
