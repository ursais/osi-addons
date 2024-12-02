# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    """
    Inherit Sale Order Object to add Credit Limit.
    """

    _inherit = "sale.order"

    @api.depends("partner_id.remaining_credit", "override_credit_limit_hold")
    def _compute_credit_hold(self):
        for order in self:
            order.credit_hold = (
                order.partner_id.credit_hold and not order.override_credit_limit_hold
            )

    @api.depends("amount_total", "invoice_status")
    def _compute_uninvoiced_balance(self):
        for order in self:
            order.uninvoiced_balance = (
                order.amount_total if order.invoice_status != "invoiced" else 0
            )

    credit_hold = fields.Boolean(
        "Credit Hold", compute="_compute_credit_hold", store=True
    )
    uninvoiced_balance = fields.Monetary(
        string="Uninvoiced Balance", compute="_compute_uninvoiced_balance", store=True
    )
    override_credit_limit_hold = fields.Boolean("Override Credit Limit Hold")

    def action_confirm(self):
        for order in self:
            if order.credit_hold and not order.override_credit_limit_hold:
                raise UserError(
                    _(
                        "Order cannot be confirmed because the customer is on credit hold."
                    )
                )
        return super().action_confirm()
