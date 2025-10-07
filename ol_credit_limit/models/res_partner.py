# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """
    Inherit Partner model to add Credit Limit management and
    related computed balances. Handles credit rollup, open SOs,
    receivables, deposits, and blanket orders.
    """

    _inherit = "res.partner"

    # COLUMNS #####

    credit_limit = fields.Float(string="Credit Limit")
    partner_rollup_id = fields.Many2one(
        "res.partner",
        string="Credit Rollup Partner",
        help="When set, any credit used on this partner will roll up to the parent partner’s credit usage.",
    )
    rollup_partner_ids = fields.One2many(
        "res.partner",
        "partner_rollup_id",
        string="Partners with this Rollup Partner",
        help="Partners that have this partner set as their Credit Rollup Partner.",
    )
    credit_hold = fields.Boolean(
        string="Credit Hold",
        compute="_compute_credit_hold",
        store=True,
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
        help="Compute the total sum of all deposits from journal items related to the partner, including its rollup partners and child contacts.",
    )
    open_bo_balance = fields.Monetary(
        string="Open BO Balance",
        store=True,
        compute="_compute_open_bo_balance",
        help="Computed sum of remaining blanket order quantities multiplied by price, for the partner and its rollup partners.",
    )
    outstanding_receivable = fields.Monetary(
        string="Outstanding Receivable",
        store=True,
        compute="_compute_outstanding_receivable",
        help="Computed sum of outstanding receivable(anything invoiced and not paid) for the partner and its rollup partners.",
    )

    # END #########
    # METHODS #####

    @api.depends(
        "total_due",
        "rollup_partner_ids.total_due",
        "rollup_partner_ids.invoice_ids.state",
        "rollup_partner_ids.invoice_ids.amount_residual",
        "invoice_ids.state",
        "invoice_ids.amount_residual",
        "rollup_partner_ids.outstanding_receivable"
    )
    def _compute_outstanding_receivable(self):
        """
        Compute total outstanding receivables for a partner,
        including rollup partner balances if applicable.
        """
        for partner in self:
            if partner.rollup_partner_ids:
                # Sum own total_due and all linked partners' total_due
                partner.outstanding_receivable = partner.total_due + sum(
                    partner.rollup_partner_ids.mapped("outstanding_receivable")
                )
            else:
                partner.outstanding_receivable = partner.total_due

    def _get_open_sale_order(self):
        """
        Compute total outstanding receivables for a partner,
        including rollup partner balances if applicable.
        """
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
        """
        Compute credit hold status:
        - Set hold if remaining credit < 0.
        - Inherit hold status from rollup partner if defined.
        """
        for partner in self:
            _logger.info("_compute_credit_hold %s", partner.id)
            # Directly compute credit hold based on remaining credit
            partner.credit_hold = partner.remaining_credit < 0

            # If the partner has a rollup partner, inherit its credit hold status
            if partner.partner_rollup_id:
                partner.credit_hold = partner.partner_rollup_id.remaining_credit < 0

    @api.depends(
        "sale_order_ids",
        "sale_order_ids.partner_id",
        "sale_order_ids.amount_total",
        "sale_order_ids.state",
        "sale_order_ids.uninvoiced_balance",
        "invoice_ids",
        "invoice_ids.amount_residual_signed",
        "invoice_ids.payment_state",
        "invoice_ids.state",
        "rollup_partner_ids.open_so_balance"
    )
    def _compute_open_so_balance(self):
        """
        Compute open Sale Order balance for the partner.
        Includes:
        - Partner's own SOs
        - Rollup partner balances
        - Handles grouping by parent, rollup, or company
        """
        
        def compute_balance_optimized(partner_ids):
            """Optimized helper to compute total SO balance for given partners."""
            if not partner_ids:
                return 0.0
            partner_ids_obj = self.browse(partner_ids)
            so_total = sum(partner_ids_obj.mapped("sale_order_ids").mapped("uninvoiced_balance"))            
            return so_total

        # Process each partner individually to avoid singleton errors
        for partner in self:
            if not partner.id:
                partner.open_so_balance = 0
                continue

            _logger.info("_compute_open_so_balance %s", partner.id)

            # Early exit for simple cases - check each partner individually
            if (
                not partner.is_company
                and not partner.partner_rollup_id
                and not partner.child_ids
            ):
                # Simple partner case
                partner.open_so_balance = compute_balance_optimized([partner.id])
                continue

            # Calculate base amounts for current partner
            open_so_total = compute_balance_optimized([partner.id])
                        
            # Calculate rollup balance safely
            rollup_balance = 0
            if partner.rollup_partner_ids:
                rollup_balance = sum(partner.rollup_partner_ids.mapped("open_so_balance"))
            
            base_balance = open_so_total + rollup_balance
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
        """
        Compute remaining credit:
        - Deduct SO balances and receivables
        - Include rollup partners’ usage
        """
        for partner in self:
            rollup_used_credit = 0
            if partner.rollup_partner_ids:
                partners_data = partner.rollup_partner_ids.read(
                    ["credit"]
                )
                rollup_credit_total = sum(
                    p.get("credit", 0.0) or 0.0 for p in partners_data
                )
                rollup_used_credit = rollup_credit_total
            used_credit = partner.credit + rollup_used_credit
            remaining_credit = partner.credit_limit - partner.open_so_balance -  used_credit or 0
            if remaining_credit <= 0:
                remaining_credit = 0
            partner.remaining_credit = remaining_credit

    @api.onchange("credit_limit")
    def onchange_credit_limit(self):
        """
        Reset rollup partner if a valid credit limit is set directly.
        """
        if self.credit_limit >= 0:
            self.partner_rollup_id = False

    @api.constrains("partner_rollup_id")
    def check_partner_rollup_id(self):
        """
        Prevent circular rollup assignments.
        """
        for partner in self:
            # Guard against empty partner_rollup_id
            if not partner.partner_rollup_id:
                continue

            if partner.id == partner.partner_rollup_id.partner_rollup_id.id:
                raise UserError(
                    _(
                        "You cannot set a Rollup Partner since this contact "
                        "has related Rollup Partners."
                    )
                )

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        """
        Custom name_search:
        - Exclude self when choosing rollup partner.
        """
        args = args or []
        if self.env.context.get("is_rollup_partner"):
            args += [("id", "!=", int(self.env.context.get("is_rollup_partner")))]
        return super().name_search(name=name, args=args, operator=operator, limit=limit)

    def _get_deposit_accounts(self):
        """
        Fetch account IDs used for deposit tracking.
        """
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
        "rollup_partner_ids.invoice_ids",
        "rollup_partner_ids.invoice_ids.payment_state",
    )
    def _compute_customer_deposit_balance(self):
        """
        Compute customer deposits:
        - Query account move lines linked to down payments
        - Include child and rollup partners
        """
        deposit_accounts = self._get_deposit_accounts()
        for partner in self:
            partners_to_include = (
                partner.rollup_partner_ids + partner._origin + partner.child_ids
            )
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

    @api.depends(
        "partner_rollup_id",
        "rollup_partner_ids",
        "sale_blanket_order_ids",
        "sale_blanket_order_ids.state",
        "sale_blanket_order_ids.line_ids",
    )
    def _compute_open_bo_balance(self):
        """
        Compute blanket order balances:
        - Remaining qty * price for open blanket orders
        - Includes rollup and parent grouping logic
        """

        def compute_balance(partners):
            partner_ids = tuple(partners.ids) or (0,)
            lines = self.env["sale.blanket.order.line"].search_read(
                [
                    ("order_id.partner_id", "in", partner_ids),
                    ("order_id.state", "=", "open"),
                ],
                ["remaining_uom_qty", "price_unit"],
            )

            total = sum(l["remaining_uom_qty"] * l["price_unit"] for l in lines)
            return total

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
