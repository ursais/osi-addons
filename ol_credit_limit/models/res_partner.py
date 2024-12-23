# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    """
    Inherit Partner Object to add Credit Limit.
    """

    _inherit = "res.partner"

    # COLUMNS #####

    credit_limit = fields.Monetary(string="Credit Limit")
    partner_rollup_id = fields.Many2one(
        "res.partner",
        "Credit Rollup Partner",
        help="When set, any credit used on this partner will roll up to the parent partner’s credit usage.",
    )
    rollup_partner_ids = fields.One2many(
        "res.partner",
        "partner_rollup_id",
        string="Partners with this Rollup Partner",
        help="Partners that have this partner set as their Credit Rollup Partner.",
    )
    credit_hold = fields.Boolean(
        "Credit Hold", compute="_compute_credit_hold", store=True
    )
    open_so_balance = fields.Monetary(
        string="Open SO Balance",
        compute="_compute_open_so_balance",
        store=True,
        help="Sum of all open sale orders including rollup partner orders.",
    )
    remaining_credit = fields.Monetary(
        string="Remaining Credit",
        compute="_compute_remaining_credit",
        store=True,
        help="Credit Remaining after sum of total_due plus all credit rollup partner’s total dues.",
    )

    # END #########
    # METHODS #####

    def _get_open_sale_order(self):
        open_so = self.sale_order_ids.filtered(lambda so: so.invoice_status != "invoiced" and so.state != "cancel")
        sorted_orders_asc = self.env['sale.order'].browse(open_so.ids).sorted('id')
        return sorted_orders_asc

    @api.depends(
        "credit_limit",
        "open_so_balance",
        "credit_hold",
        "partner_rollup_id",
        "remaining_credit",
    )
    def _compute_credit_hold(self):
        for partner in self:
            open_so= partner._get_open_sale_order()
            if partner:
                partner.credit_hold = partner.remaining_credit < 0
                if partner.partner_rollup_id:
                    partner.credit_hold = partner.partner_rollup_id.remaining_credit < 0

    @api.depends(
        "sale_order_ids",
        "sale_order_ids.partner_id",
        "sale_order_ids.amount_total",
        "sale_order_ids.invoice_status",
        "sale_order_ids.state",
        "rollup_partner_ids.sale_order_ids.invoice_status",
        "invoice_ids",
        "invoice_ids.amount_residual_signed",
        "invoice_ids.payment_state",
        "invoice_ids.state",
    )
    def _compute_open_so_balance(self):
        all_child = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
        for partner in self:
            open_so= partner._get_open_sale_order()
            not_paid_invoices = self.env["account.move"].search([('move_type', '=', 'out_invoice'),('partner_id', 'in', all_child.ids),("state","=","draft")])
            open_so_balance = partner.rollup_partner_ids.mapped("open_so_balance")
            partner.open_so_balance = sum(open_so.mapped('amount_total'))+ sum(open_so_balance) + sum(not_paid_invoices.mapped("amount_residual_signed"))

    @api.depends(
        "credit_limit", "total_due", "rollup_partner_ids.total_due", "partner_rollup_id", "invoice_ids","open_so_balance",
        "invoice_ids.amount_residual_signed",
        "invoice_ids.payment_state",
        "invoice_ids.state",
        "sale_order_ids.amount_total",
        "sale_order_ids.invoice_status",
        "sale_order_ids.partner_id",
        "sale_order_ids.state"
    )
    def _compute_remaining_credit(self):
        for partner in self:
            credit = (partner.credit > 0 and partner.credit or 0)
            used_credit = partner.open_so_balance + credit
            if partner.rollup_partner_ids:
                used_credit = sum(partner.mapped('rollup_partner_ids.open_so_balance')) + sum(partner.mapped('rollup_partner_ids.credit')) + credit
            partner.remaining_credit = partner.credit_limit - used_credit or 0

    @api.onchange("credit_limit")
    def onchange_credit_limit(self):
        if self.credit_limit >= 0:
            self.partner_rollup_id = False

    @api.constrains("partner_rollup_id")
    def check_partner_rollup_id(self):
        if self.id == self.partner_rollup_id.partner_rollup_id.id:
            raise UserError(
                _(
                    "You cannot set a Rollup Partner since this contact has related Rollup Partners."
                )
            )

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        # Call super to get the original name_search result
        args = args or []
        if self.env.context.get("is_rollup_partner"):
            args += [("id", "!=", int(self.env.context.get("is_rollup_partner")))]
        return super().name_search(name=name, args=args, operator=operator, limit=limit)

    # END #########
