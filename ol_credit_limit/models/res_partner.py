# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """
    Inherit Partner Object to add Credit Limit.
    """

    _inherit = "res.partner"

    # COLUMNS #####

    # credit_limit = fields.Monetary(string="Credit Limit")
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
    customer_deposit_balance = fields.Monetary(
        string="Customer Deposit Balance",
        store=True,
        compute="_compute_customer_deposit_balance",
        help="Computed sum of all deposits from relevant journal items for the partner and its rollup partners.",
    )
    open_bo_balance = fields.Monetary(
        string="Open BO Balance",
        store=True,
        compute="_compute_open_bo_balance",
        help="Computed sum of remaining blanket order quantities multiplied by price, for the partner and its rollup partners.",
    )

    # END #########
    # METHODS #####

    def _get_open_sale_order(self):
        query = """
            SELECT COALESCE(SUM(amount_total), 0)
            FROM sale_order
            WHERE partner_id = %s
            AND invoice_status != 'invoiced'
            AND state != 'cancel'
        """
        self.env.cr.execute(query, (self.id,))
        total_amount = self.env.cr.fetchone()[0]
        return total_amount

    @api.depends(
        "credit_limit",
        "open_so_balance",
        "credit_hold",
        "partner_rollup_id.remaining_credit",
        "remaining_credit",
    )
    def _compute_credit_hold(self):
        for partner in self:
            _logger.info("_compute_credit_hold %s", partner.id)
            # Directly compute credit hold based on remaining credit
            partner.credit_hold = partner.remaining_credit < 0

            # If the partner has a rollup partner, inherit its credit hold status
            if partner.partner_rollup_id:
                partner.credit_hold = partner.partner_rollup_id.remaining_credit < 0

    # @api.depends(
    #     "sale_order_ids",
    #     "sale_order_ids.partner_id",
    #     "sale_order_ids.amount_total",
    #     "sale_order_ids.invoice_status",
    #     "sale_order_ids.state",
    #     "rollup_partner_ids.sale_order_ids.invoice_status",
    #     "invoice_ids",
    #     "invoice_ids.amount_residual_signed",
    #     "invoice_ids.payment_state",
    #     "invoice_ids.state",
    # )
    # def _compute_open_so_balance(self):
    #     all_child = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
    #     for partner in self:
    #         open_so= partner._get_open_sale_order()
    #         not_paid_invoices = self.env["account.move"].search([('move_type', '=', 'out_invoice'),('partner_id', 'in', all_child.ids),("state","=","draft")])
    #         open_so_balance = partner.rollup_partner_ids.mapped("open_so_balance")
    #         partner.open_so_balance = sum(open_so.mapped('amount_total'))+ sum(open_so_balance) + sum(not_paid_invoices.mapped("amount_residual_signed"))

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
        self.filtered(lambda l: not l.credit_limit).open_so_balance = 0
        for partner in self.filtered(lambda l: l.credit_limit):
            # Use raw SQL query to get all child IDs efficiently
            self.env.cr.execute(
                """
                SELECT id FROM res_partner WHERE parent_id in %s
            """,
                (tuple(partner.ids),),
            )
            all_child_ids = [row[0] for row in self.env.cr.fetchall()]
            all_child_ids.append(partner.id)
            _logger.info("_compute_open_so_balance %s", partner.id)
            open_so = partner._get_open_sale_order()

            # Aggregate draft invoices using raw SQL query
            not_paid_invoices = 0

            self.env.cr.execute(
                """
                SELECT COALESCE(SUM(amount_residual_signed), 0) 
                FROM account_move 
                WHERE move_type = 'out_invoice' 
                AND partner_id IN %s 
                AND state = 'draft'
            """,
                (tuple(all_child_ids),),
            )
            not_paid_invoices = self.env.cr.fetchone()[0] or 0

            open_so_balance = (
                open_so
                + sum(partner.rollup_partner_ids.mapped("open_so_balance"))
                + not_paid_invoices
            )

            partner.open_so_balance = open_so_balance

    @api.depends(
        "credit_limit",
        "total_due",
        "rollup_partner_ids.total_due",
        "partner_rollup_id",
        "invoice_ids",
        "open_so_balance",
        "invoice_ids.amount_residual_signed",
        "invoice_ids.payment_state",
        "invoice_ids.state",
        "sale_order_ids.amount_total",
        "sale_order_ids.invoice_status",
        "sale_order_ids.partner_id",
        "sale_order_ids.state",
    )
    def _compute_remaining_credit(self):
        self.filtered(lambda l: not l.credit_limit).remaining_credit = 0
        for partner in self.filtered(lambda l: l.credit_limit):
            _logger.info("_compute_remaining_credit %s", partner.id)
            # print ("\n ------_compute_remaining_credit------",)
            rollup_used_credit = 0
            if partner.rollup_partner_ids:
                rollup_credit_data = partner.rollup_partner_ids.read_group(
                    [], ["open_so_balance:sum", "credit:sum"], []
                )
                rollup_used_credit = (
                    sum(rollup_credit_data[0].values()) if rollup_credit_data else 0
                )

            used_credit = (
                partner.open_so_balance
                + (partner.credit if partner.credit > 0 else 0)
                + rollup_used_credit
            )
            partner.remaining_credit = (
                partner.credit_limit - used_credit if partner.credit_limit else 0
            )

    # @api.depends(
    #     "credit_limit", "total_due", "rollup_partner_ids.total_due", "partner_rollup_id", "invoice_ids","open_so_balance",
    #     "invoice_ids.amount_residual_signed",
    #     "invoice_ids.payment_state",
    #     "invoice_ids.state",
    #     "sale_order_ids.amount_total",
    #     "sale_order_ids.invoice_status",
    #     "sale_order_ids.partner_id",
    #     "sale_order_ids.state"
    # )
    # def _compute_remaining_credit(self):
    #     for partner in self:
    #         credit = (partner.credit > 0 and partner.credit or 0)
    #         used_credit = partner.open_so_balance + credit
    #         if partner.rollup_partner_ids:
    #             used_credit = sum(partner.mapped('rollup_partner_ids.open_so_balance')) + sum(partner.mapped('rollup_partner_ids.credit')) + credit
    #         partner.remaining_credit = partner.credit_limit - used_credit or 0

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

    def _get_deposit_accounts(self):
        query_accounts = """
            SELECT id FROM account_account
            WHERE account_type = 'asset_receivable' AND deprecated = FALSE
        """
        self.env.cr.execute(query_accounts)
        deposit_accounts = tuple(row[0] for row in self.env.cr.fetchall())
        return deposit_accounts

    @api.depends(
        "partner_rollup_id",
        "rollup_partner_ids",
        "invoice_ids.line_ids.account_id",
        "invoice_ids.line_ids.balance",
    )
    def _compute_customer_deposit_balance(self):
        deposit_accounts = self._get_deposit_accounts()
        for partner in self:
            _logger.info("_compute_customer_deposit_balance %s", partner.id)
            partners_to_include = tuple(partner.rollup_partner_ids.ids + [partner.id])
            # if not partners_to_include or not deposit_accounts:
            #     partner.customer_deposit_balance = 0.0
            #     continue

            query = """
                SELECT SUM(aml.balance) * -1
                FROM account_move_line aml
                WHERE aml.partner_id IN %s
                AND aml.account_id IN %s
                AND aml.balance < 0
            """

            self.env.cr.execute(query, (partners_to_include, deposit_accounts))
            result = self.env.cr.fetchone()[0] or 0.0
            partner.customer_deposit_balance = result

    @api.depends(
        "partner_rollup_id",
        "rollup_partner_ids",
        "sale_order_ids.order_line.product_uom_qty",
        "sale_order_ids.order_line.price_unit",
        "sale_order_ids.order_line.state",
        "rollup_partner_ids.sale_order_ids.order_line.product_uom_qty",
        "rollup_partner_ids.sale_order_ids.order_line.price_unit",
    )
    def _compute_open_bo_balance(self):
        for partner in self:
            _logger.info("_compute_open_bo_balance %s", partner.id)
            partners_to_include = tuple(partner.rollup_partner_ids.ids + [partner.id])
            query = """
                SELECT SUM(sol.product_uom_qty * sol.price_unit)
                FROM sale_order_line sol
                JOIN sale_order so ON sol.order_id = so.id
                WHERE so.partner_id IN %s
                AND sol.blanket_order_line IS NOT NULL
                AND so.state NOT IN ('cancel', 'done')
                AND sol.product_uom_qty > 0
            """

            self.env.cr.execute(query, (partners_to_include,))
            result = self.env.cr.fetchone()[0] or 0.0
            partner.open_bo_balance = result

    # def _compute_open_bo_balance(self):
    #     SOL = self.env["sale.order.line"]
    #     for partner in self:
    #         partners_to_include = partner.rollup_partner_ids | partner
    #         domain = [
    #         ("order_id.partner_id","in",partners_to_include.ids),
    #         ("blanket_order_line","!=",False),
    #         ("order_id.state","not in",["cancel","done"]),
    #         ("product_uom_qty",">",0),
    #         ]
    #         bo_balance = sum(SOL.search(domain).mapped(lambda l:l.product_uom_qty * l.price_unit))
    #         partner.open_bo_balance = bo_balance

    # END #########
