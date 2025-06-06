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
        "Credit Hold", compute="_compute_ol_credit_limit_all", store=True
    )
    # compute="_compute_credit_hold"
    open_so_balance = fields.Monetary(
        string="Open SO Balance",
        # compute="_compute_open_so_balance",
        compute="_compute_ol_credit_limit_all",
        store=True,
        help="Sum of all open sale orders including rollup partner orders.",
    )
    remaining_credit = fields.Monetary(
        string="Remaining Credit",
        # compute="_compute_remaining_credit",
        compute="_compute_ol_credit_limit_all",
        store=True,
        help="Credit Remaining after sum of total_due plus all credit rollup partner’s total dues.",
    )
    customer_deposit_balance = fields.Monetary(
        string="Customer Deposit Balance",
        store=True,
        # compute="_compute_customer_deposit_balance",
        compute="_compute_ol_credit_limit_all",
        help="Computed sum of all deposits from relevant journal items for the partner and its rollup partners.",
    )
    open_bo_balance = fields.Monetary(
        string="Open BO Balance",
        store=True,
        # compute="_compute_open_bo_balance",
        compute="_compute_ol_credit_limit_all",
        help="Computed sum of remaining blanket order quantities multiplied by price, for the partner and its rollup partners.",
    )

    # END #########
    # METHODS #####


    @api.depends(
        "credit_limit",
        "open_so_balance",
        "credit_hold",
        "partner_rollup_id.remaining_credit",
        "remaining_credit",
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
        "total_due",
        "rollup_partner_ids.total_due",
        "partner_rollup_id",
        "rollup_partner_ids",
        "invoice_ids.line_ids.account_id",
        "invoice_ids.line_ids.balance",
        "invoice_ids.payment_ids",
        "partner_rollup_id",
        "sale_blanket_order_ids",
        "sale_blanket_order_ids.state",
        "sale_blanket_order_ids.line_ids",
    )
    def _compute_ol_credit_limit_all(self): 
        cr = self.env.cr
        ICP = self.env['ir.config_parameter'].sudo()
        COUNTER = int(ICP.get_param('global_counter', 0))
        def compute_balance(partners):
            lines = partners.sale_blanket_order_ids.filtered(
                lambda l: l.state == "open"
            ).mapped("line_ids")
            return sum(line.remaining_uom_qty * line.price_unit for line in lines)
        #Prefetch all Compute Data:
        # Step 1: Precompute sale order totals by partner (only 'sale' and not invoiced)
        cr.execute("""
            SELECT partner_id, SUM(amount_total)
            FROM sale_order
            WHERE state = 'sale' AND invoice_status = 'no'
            GROUP BY partner_id
        """)
        so_totals_by_partner = dict(self.env.cr.fetchall())  # {partner_id: total}

        # Step 2: Precompute draft invoice totals
        cr.execute("""
            SELECT partner_id, SUM(amount_residual_signed)
            FROM account_move
            WHERE move_type = 'out_invoice' AND state = 'draft'
            GROUP BY partner_id
        """)
        draft_invoice_totals = dict(self.env.cr.fetchall())
        update_values = []
        for partner in self:
            partner_id = partner.id
            COUNTER += 1
            _logger.info("_compute_credit_hold %s", partner_id)
            # Directly compute credit hold based on remaining credit
            credit_hold_self = partner.remaining_credit < 0
            update_query = "UPDATE res_partner SET credit_hold = %s where id = %s;"
            # cr.execute(update_query,(credit_hold,partner_id))
            update_values.append((credit_hold_self, partner_id))
            if partner.partner_rollup_id:
                credit_hold_rollup = partner.partner_rollup_id.remaining_credit < 0
                # cr.execute(update_query,(credit_hold,partner.partner_rollup_id.id))
                update_values.append((credit_hold_rollup, partner.partner_rollup_id.id))
            # =============================================================
            _logger.info("_compute_open_so_balance %s Counter %s", partner_id,COUNTER)
            open_so_total = so_totals_by_partner.get(partner_id, 0.0)
            draft_invoice_total = draft_invoice_totals.get(partner_id, 0.0)

            rollup_balance = sum([
                so_totals_by_partner.get(p.id, 0.0)
                for p in partner.rollup_partner_ids
            ])
            base_balance = open_so_total + draft_invoice_total + rollup_balance

            if partner.sale_order_ids:
                if partner.is_company:
                    full_group = partner | partner.child_ids | partner.rollup_partner_ids
                    query = "UPDATE res_partner set open_so_balance = %s where id = %s;"
                    open_so_balance = sum([
                        so_totals_by_partner.get(p.id, 0.0)
                        for p in full_group
                    ])
                    cr.execute(query,(open_so_balance,partner_id))
                elif partner.partner_rollup_id and not partner.parent_id:
                    query = "UPDATE res_partner set open_so_balance = %s where id = %s;"
                    rollup_group = (
                        partner.partner_rollup_id
                        | partner.partner_rollup_id.child_ids
                        | partner
                    )
                    open_so_balance = sum([
                        so_totals_by_partner.get(p.id, 0.0)
                        for p in rollup_group
                    ])
                    cr.execute(query,(base_balance,partner_id))
                    cr.execute(query,(open_so_balance,partner.partner_rollup_id.id))
                elif partner.parent_id and not partner.partner_rollup_id:
                    query = "UPDATE res_partner set open_so_balance = %s where id = %s;"
                    cr.execute(query,(base_balance,partner_id))
                    parent_group = (
                        partner.parent_id
                        | partner.parent_id.child_ids
                        | partner.parent_id.rollup_partner_ids
                    )
                    parent_balance = sum([
                        so_totals_by_partner.get(p.id, 0.0)
                        for p in parent_group
                    ])
                    # partner.open_so_balance = base_balance
                    cr.execute(query,(parent_balance, partner.parent_id.id))
                # partner.parent_id.open_so_balance = parent_balance
            else:
                query = "UPDATE res_partner set open_so_balance = %s where id = %s;"
                cr.execute(query,(0.0,partner_id))
            # =============================================================
            _logger.info("_compute_remaining_credit %s Counter: %s", partner_id,COUNTER)
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
            remaining_credit = (
                partner.credit_limit - used_credit if partner.credit_limit else 0
            )
            # =============================================================
            _logger.info("_compute_customer_deposit_balance %s Counter: %s", partner_id,COUNTER)
            partners_to_include = partner.rollup_partner_ids + partner._origin
            invoice_line_ids = partners_to_include.invoice_ids.mapped(
                "invoice_line_ids"
            ).filtered(
                lambda l: l.product_id.id
                == l.company_id.sale_down_payment_product_id.id
                and not l.full_reconcile_id
            )
            customer_deposit_balance = sum(invoice_line_ids.mapped("balance"))
            customer_deposit_balance = customer_deposit_balance * -1
            update_query = "UPDATE res_partner SET remaining_credit = %s , customer_deposit_balance = %s where id = %s;"
            cr.execute(update_query,(remaining_credit,customer_deposit_balance,partner_id))
            # =============================================================
            _logger.info("_compute_open_bo_balance %s Conter : %s", partner._origin.id,COUNTER)

            partners_base = partner._origin
            base_balance = compute_balance(partners_base)

            if partners_base.sale_blanket_order_ids:
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
            else:
                partner.open_bo_balance = 0.0
            _logger.info("Whole Compution Process Done")
        update_query = "UPDATE res_partner SET credit_hold = %s WHERE id = %s"
        cr.executemany(update_query, update_values)
        self.env['ir.config_parameter'].set_param('global_counter', COUNTER)

    # def _get_open_sale_order(self):
    #     """Method is used for Get Open Sale Orders based on Partners!"""
    #     open_so_balance = self.env["sale.order"]
    #     if not self:
    #         return open_so_balance
    #     open_so_balance = self.sale_order_ids.filtered(
    #         lambda l: l.state == "sale" and l.invoice_status == "no"
    #     )
    #     return open_so_balance

    # @api.depends(
    #     "credit_limit",
    #     "open_so_balance",
    #     "credit_hold",
    #     "partner_rollup_id.remaining_credit",
    #     "remaining_credit",
    # )
    # def _compute_credit_hold(self):
    #     for partner in self:
    #         _logger.info("_compute_credit_hold %s", partner.id)
    #         # Directly compute credit hold based on remaining credit
    #         partner.credit_hold = partner.remaining_credit < 0

    #         # If the partner has a rollup partner, inherit its credit hold status
    #         if partner.partner_rollup_id:
    #             partner.credit_hold = partner.partner_rollup_id.remaining_credit < 0

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
    #     def compute_balance(partners):
    #         open_so = partners._get_open_sale_order()
    #         return sum(open_so.mapped("amount_total"))

    #     for partner in self:
    #         if not partner.id:
    #             partner.open_so_balance = 0
    #             continue

    #         _logger.info("_compute_open_so_balance %s", partner.id)

    #         # Collect all relevant partner IDs: self + children
    #         self.env.cr.execute(
    #             "SELECT id FROM res_partner WHERE parent_id = ANY(%s)", ([partner.id],),
    #         )
    #         child_ids = [row[0] for row in self.env.cr.fetchall()]
    #         all_partner_ids = child_ids + [partner.id]

    #         # Calculate open SO total and draft invoice amount
    #         open_so_total = compute_balance(partner._origin)
    #         self.env.cr.execute(
    #             """
    #             SELECT COALESCE(SUM(amount_residual_signed), 0)
    #             FROM account_move
    #             WHERE move_type = 'out_invoice'
    #               AND state = 'draft'
    #               AND partner_id = ANY(%s)
    #             """,
    #             ([all_partner_ids],),
    #         )
    #         draft_invoice_total = self.env.cr.fetchone()[0] or 0
    #         rollup_balance = sum(partner.rollup_partner_ids.mapped("open_so_balance"))

    #         base_balance = open_so_total + draft_invoice_total + rollup_balance

    #         if partner._origin.is_company:
    #             full_group = (
    #                 partner.rollup_partner_ids | partner.child_ids | partner._origin
    #             )
    #             partner.open_so_balance = compute_balance(full_group)

    #         elif partner.partner_rollup_id and not partner.parent_id:
    #             rollup_group = (
    #                 partner.partner_rollup_id
    #                 | partner.partner_rollup_id.child_ids
    #                 | partner._origin
    #             )
    #             partner.open_so_balance = base_balance
    #             partner.partner_rollup_id.open_so_balance = compute_balance(
    #                 rollup_group
    #             )

    #         elif partner.parent_id and not partner.partner_rollup_id:
    #             parent_group = (
    #                 partner.parent_id
    #                 | partner.parent_id.child_ids
    #                 | partner.parent_id.rollup_partner_ids
    #             )
    #             parent_balance = compute_balance(parent_group)
    #             partner.parent_id.open_so_balance = parent_balance
    #             partner.open_so_balance = base_balance

    # @api.depends(
    #     "credit_limit",
    #     "total_due",
    #     "rollup_partner_ids.total_due",
    #     "partner_rollup_id",
    #     "invoice_ids",
    #     "open_so_balance",
    #     "invoice_ids.amount_residual_signed",
    #     "invoice_ids.payment_state",
    #     "invoice_ids.state",
    #     "sale_order_ids.amount_total",
    #     "sale_order_ids.invoice_status",
    #     "sale_order_ids.partner_id",
    #     "sale_order_ids.state",
    # )
    # def _compute_remaining_credit(self):
    #     self.filtered(lambda l: not l.credit_limit).remaining_credit = 0
    #     for partner in self.filtered(lambda l: l.credit_limit):
    #         _logger.info("_compute_remaining_credit %s", partner.id)
    #         rollup_used_credit = 0
    #         if partner.rollup_partner_ids:
    #             rollup_credit_data = partner.rollup_partner_ids.read_group(
    #                 [], ["open_so_balance:sum", "credit:sum"], []
    #             )
    #             rollup_used_credit = (
    #                 sum(rollup_credit_data[0].values()) if rollup_credit_data else 0
    #             )

    #         used_credit = (
    #             partner.open_so_balance
    #             + (partner.credit if partner.credit > 0 else 0)
    #             + rollup_used_credit
    #         )
    #         partner.remaining_credit = (
    #             partner.credit_limit - used_credit if partner.credit_limit else 0
    #         )

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

    # @api.depends(
    #     "partner_rollup_id",
    #     "rollup_partner_ids",
    #     "invoice_ids.line_ids.account_id",
    #     "invoice_ids.line_ids.balance",
    #     "invoice_ids.payment_ids",
    #     "invoice_ids.payment_state",
    # )
    # def _compute_customer_deposit_balance(self):
    #     deposit_accounts = self._get_deposit_accounts()
    #     for partner in self:
    #         partners_to_include = partner.rollup_partner_ids + partner._origin
    #         invoice_line_ids = partners_to_include.invoice_ids.mapped(
    #             "invoice_line_ids"
    #         ).filtered(
    #             lambda l: l.product_id.id
    #             == l.company_id.sale_down_payment_product_id.id
    #             and not l.full_reconcile_id
    #         )
    #         customer_deposit_balance = sum(invoice_line_ids.mapped("balance"))
    #         customer_deposit_balance = customer_deposit_balance * -1
    #         partner.customer_deposit_balance = customer_deposit_balance

    # @api.depends(
    #     "partner_rollup_id",
    #     "rollup_partner_ids",
    #     "sale_blanket_order_ids",
    #     "sale_blanket_order_ids.state",
    #     "sale_blanket_order_ids.line_ids",
    # )
    # def _compute_open_bo_balance(self):
    #     def compute_balance(partners):
    #         lines = partners.sale_blanket_order_ids.filtered(
    #             lambda l: l.state == "open"
    #         ).mapped("line_ids")
    #         return sum(line.remaining_uom_qty * line.price_unit for line in lines)

    #     for partner in self:
    #         _logger.info("_compute_open_bo_balance %s", partner._origin.id)

    #         partners_base = partner._origin
    #         base_balance = compute_balance(partners_base)

    #         if partner._origin.is_company:
    #             partners_all = (
    #                 partner.rollup_partner_ids | partner.child_ids | partners_base
    #             )
    #             partner.open_bo_balance = compute_balance(partners_all)

    #         elif partner.partner_rollup_id and not partner.parent_id:
    #             rollup_group = (
    #                 partner.partner_rollup_id
    #                 | partner.partner_rollup_id.child_ids
    #                 | partners_base
    #             )
    #             partner.open_bo_balance = base_balance
    #             partner.partner_rollup_id.open_bo_balance = compute_balance(
    #                 rollup_group
    #             )

    #         elif partner.parent_id and not partner.partner_rollup_id:
    #             parent_group = (
    #                 partner.parent_id
    #                 | partner.parent_id.child_ids
    #                 | partner.parent_id.rollup_partner_ids
    #             )
    #             balance = compute_balance(parent_group)
    #             partner.parent_id.open_bo_balance = balance
    #             partner.open_bo_balance = base_balance

    # END #########
