# Import Odoo libs
from odoo import _, api, fields, models


class SaleOrder(models.Model):
    """
    Inherit Sale Order Object to add Credit Limit.
    """

    _inherit = "sale.order"

    # COLUMNS #####

    credit_hold = fields.Boolean(
        "Credit Hold", compute="_compute_credit_hold", store=True
    )
    uninvoiced_balance = fields.Monetary(
        string="Uninvoiced Balance", compute="_compute_uninvoiced_balance", store=True
    )
    override_credit_limit_hold = fields.Boolean("Override Credit Limit Hold")

    # END #########
    # METHODS #####

    @api.depends("partner_id.remaining_credit","partner_id.open_so_balance", "override_credit_limit_hold")
    def _compute_credit_hold(self):
        open_saleorders = self.partner_id._get_open_sale_order()
        counter_total = 0
        credit_hold = False
        for order in open_saleorders:
            counter_total += order.amount_total
            if counter_total > order.partner_id.credit_limit:
                credit_hold = True
            if order.override_credit_limit_hold:
                credit_hold = False
            order.credit_hold = credit_hold
            

    @api.depends("amount_total", "invoice_status")
    def _compute_uninvoiced_balance(self):
        for order in self:
            order.uninvoiced_balance = (
                order.amount_total if order.invoice_status != "invoiced" else 0
            )

    # END #########
