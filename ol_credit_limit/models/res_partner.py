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
        """Method is used for Get Open Sale Orders based on Partners!"""
        open_so_balance = self.env["sale.order"]
        if not self:
            return open_so_balance
        open_so_balance = self.sale_order_ids.filtered(
            lambda l: l.state == "sale" and l.invoice_status == "no"
        )
        return open_so_balance

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
        def compute_balance(partners):
            self.env.cr.execute("""
                SELECT SUM(amount_total)
                FROM sale_order
                WHERE state = 'sale'
                AND invoice_status = 'no'
                AND partner_id in %s
            """, (tuple(self.ids),))

            so_sum = self.env.cr.fetchone()[0] or 0.0
            
            return so_sum


        for partner in self:

            if not partner.id:
                partner.open_so_balance = 0
                continue

            _logger.info("_compute_open_so_balance %s", partner.id)

            # Collect all relevant partner IDs: self + children
            self.env.cr.execute(
                "SELECT id FROM res_partner WHERE parent_id = ANY(%s)", ([partner.id],),
            )
            child_ids = [row[0] for row in self.env.cr.fetchall()]
            all_partner_ids = child_ids + [partner.id]

            # Calculate open SO total and draft invoice amount
            open_so_total = compute_balance(partner._origin)
            self.env.cr.execute(
                """
                SELECT COALESCE(SUM(amount_residual_signed), 0)
                FROM account_move
                WHERE move_type = 'out_invoice'
                  AND state = 'draft'
                  AND partner_id = ANY(%s)
                """,
                ([all_partner_ids],),
            )
            draft_invoice_total = self.env.cr.fetchone()[0] or 0
            rollup_balance = sum(partner.rollup_partner_ids.mapped("open_so_balance"))

            base_balance = open_so_total + draft_invoice_total + rollup_balance

            if partner._origin.is_company:
                full_group = (
                    partner.rollup_partner_ids | partner.child_ids | partner._origin
                )
                partner.open_so_balance = compute_balance(full_group)

            elif partner.partner_rollup_id and not partner.parent_id:
                rollup_group = (
                    partner.partner_rollup_id
                    | partner.partner_rollup_id.child_ids
                    | partner._origin
                )
                partner.open_so_balance = base_balance
                partner.partner_rollup_id.open_so_balance = compute_balance(
                    rollup_group
                )

            elif partner.parent_id and not partner.partner_rollup_id:
                parent_group = (
                    partner.parent_id
                    | partner.parent_id.child_ids
                    | partner.parent_id.rollup_partner_ids
                )
                parent_balance = compute_balance(parent_group)
                partner.parent_id.open_so_balance = parent_balance
                partner.open_so_balance = base_balance

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
        for partner in self:
            if not partner.credit_limit:
                partner.remaining_credit = 0
            else:
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
                    partner.credit_limit - used_credit or 0
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
        "invoice_ids.payment_ids",
        "invoice_ids.payment_state",
    )
    def _compute_customer_deposit_balance(self):
        deposit_accounts = self._get_deposit_accounts()
        for partner in self:
            partners_to_include = partner.rollup_partner_ids + partner._origin
            invoice_line_ids = partners_to_include.invoice_ids.mapped(
                "invoice_line_ids"
            )
            if invoice_line_ids:
                ids_tuple = tuple(invoice_line_ids.ids)
            else:
                ids_tuple = (0,)
            query = """
                SELECT COALESCE(SUM(aml.balance), 0)
                FROM account_move_line aml
                JOIN res_company rc ON aml.company_id = rc.id
                WHERE aml.id IN %s
                AND aml.product_id = rc.sale_down_payment_product_id
                AND aml.full_reconcile_id IS NULL
            """
            self.env.cr.execute(query, (ids_tuple,))
            customer_deposit_balance = self.env.cr.fetchone()[0] or 0
            customer_deposit_balance = customer_deposit_balance * -1
            partner.customer_deposit_balance = customer_deposit_balance

    # @api.depends(
    #     "partner_rollup_id",
    #     "rollup_partner_ids",
    #     "sale_order_ids.order_line.product_uom_qty",
    #     "sale_order_ids.order_line.price_unit",
    #     "sale_order_ids.order_line.state",
    #     "rollup_partner_ids.sale_order_ids.order_line.product_uom_qty",
    #     "rollup_partner_ids.sale_order_ids.order_line.price_unit",
    # )
    # def _compute_open_bo_balance(self):
    #     for partner in self:
    #         _logger.info("_compute_open_bo_balance %s", partner._origin.id)
    #         partners_to_include = tuple(partner.rollup_partner_ids.ids + [ partner._origin.id])
    #         query = """
    #             SELECT SUM(sol.product_uom_qty * sol.price_unit)
    #             FROM sale_order_line sol
    #             JOIN sale_order so ON sol.order_id = so.id
    #             WHERE so.partner_id IN %s
    #             AND sol.blanket_order_line IS NOT NULL
    #             AND so.state NOT IN ('cancel', 'done')
    #             AND sol.product_uom_qty > 0
    #         """
    #         self.env.cr.execute(query, (partners_to_include,))
    #         result = self.env.cr.fetchone()[0] or 0.0
    #         partner.open_bo_balance = result

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

    @api.depends(
        "partner_rollup_id",
        "rollup_partner_ids",
        "sale_blanket_order_ids",
        "sale_blanket_order_ids.state",
        "sale_blanket_order_ids.line_ids",
    )
    def _compute_open_bo_balance(self):
        def compute_balance(partners):
            partner_ids = tuple(partners.ids) or (0,)
            self.env.cr.execute("""
                SELECT COALESCE(SUM(l.remaining_uom_qty * l.price_unit), 0)
                FROM sale_blanket_order_line l
                JOIN sale_blanket_order o ON l.order_id = o.id
                WHERE o.partner_id IN %s
                AND o.state = 'open'
            """, (partner_ids,))
            return self.env.cr.fetchone()[0]
        for partner in self:
            

            partners_base = partner._origin
            base_balance = compute_balance(partners_base)

            if partner._origin.is_company:
                partners_all = (
                    partner.rollup_partner_ids | partner.child_ids | partners_base
                )
                partner.open_bo_balance = compute_balance(partners_all)

            elif partner.partner_rollup_id and not partner.parent_id:
                rollup_group = (
                    partner.partner_rollup_id
                    | partner.partner_rollup_id.child_ids
                    | partners_base
                )
                partner.open_bo_balance = base_balance
                partner.partner_rollup_id.open_bo_balance = compute_balance(
                    rollup_group
                )

            elif partner.parent_id and not partner.partner_rollup_id:
                parent_group = (
                    partner.parent_id
                    | partner.parent_id.child_ids
                    | partner.parent_id.rollup_partner_ids
                )
                balance = compute_balance(parent_group)
                partner.parent_id.open_bo_balance = balance
                partner.open_bo_balance = base_balance


    # END #########
