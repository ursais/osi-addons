# Import Odoo libs
from odoo import _, api, fields, models


class SaleOrder(models.Model):
    """
    Inherit Sale Order to add Credit Limit functionality.

    Adds:
      - Credit hold status per order
      - Uninvoiced balance calculation
      - Override flag for credit hold
    """

    _inherit = "sale.order"

    # COLUMNS #####

    credit_hold = fields.Boolean(
        string="Credit Hold",
        compute="_compute_credit_hold",
        store=True,
    )
    uninvoiced_balance = fields.Monetary(
        string="Uninvoiced Balance",
        compute="_compute_uninvoiced_balance",
        store=True,
    )
    override_credit_limit_hold = fields.Boolean("Override Credit Limit Hold")

    # END #########
    # METHODS #####

    def _get_open_sale_order(self, partner_ids):
        """
        Fetch open Sale Orders for given partners.

        Criteria:
          - Partner matches
          - Not fully invoiced
          - Not cancelled or draft

        Returns a recordset of sale orders.
        """
        so_obj = self.env["sale.order"]
        if not partner_ids:
            return so_obj
        # Normalize partner_ids to a list of IDs
        if hasattr(partner_ids, "ids"):
            p_ids = tuple(partner_ids.ids) or (0,)
        else:
            p_ids = tuple(partner_ids) or (0,)
        query = """
            SELECT id
            FROM sale_order
            WHERE partner_id IN %s
            AND invoice_status != 'invoiced'
            AND state not in ('cancel','draft')
        """
        self.env.cr.execute(query, (p_ids,))
        so_list = [so[0] for so in self.env.cr.fetchall()]
        return so_obj.browse(so_list)

    @api.depends(
        "partner_id.remaining_credit",
        "partner_id.open_so_balance",
        "override_credit_limit_hold",
    )
    def _compute_credit_hold(self):
        """
        Multi-record-safe version:
        - Groups by partner so we compute credit usage once per partner.
        - Evaluates open orders + orders referenced by unpaid invoices,
        ordered by original_request_date (oldest first).
        - Marks orders as credit hold if cumulative usage > partner.credit_limit,
        unless override_credit_limit_hold or order is already paid.
        """
        if not self:
            return

        # Map partner -> its sale.order records that we need to set
        partner_to_orders = {}
        for order in self:
            partner_to_orders.setdefault(order.partner_id.id, []).append(order)

        # For each partner, compute the credit logic once
        order_hold_map = {}  # order.id -> bool
        for partner_id, orders in partner_to_orders.items():
            partner = orders[0].partner_id

            # Build full partner id set: partner + children + rollup partners
            partner_set = set([partner.id])
            partner_set.update(partner.child_ids.ids)
            partner_set.update(partner.rollup_partner_ids.ids)
            partner_ids = list(partner_set) or [partner.id]

            # Fetch open sale orders for these partner ids
            open_saleorders = self.env["sale.order"].search(
                [
                    ("partner_id", "in", partner_ids),
                    ("invoice_status", "!=", "invoiced"),
                    ("state", "not in", ("cancel", "draft")),
                ]
            )

            # Unpaid invoices and related orders
            not_paid_invoices = self.env["account.move"].search(
                [
                    ("move_type", "=", "out_invoice"),
                    ("partner_id", "in", partner_ids),
                    ("state", "!=", "cancel"),
                ]
            )
            open_so_invoices = not_paid_invoices.mapped(
                "line_ids.sale_line_ids.order_id"
            )

            # Paid invoices (so we can ignore already-paid orders)
            paid_invoices = self.env["account.move"].search(
                [
                    ("move_type", "=", "out_invoice"),
                    ("partner_id", "in", partner_ids),
                    ("state", "!=", "cancel"),
                    ("payment_state", "in", ["in_payment", "paid"]),
                ]
            )
            paid_so_invoices = paid_invoices.mapped("line_ids.sale_line_ids.order_id")

            # Combine orders (unique) and sort by request date
            saleorders = open_saleorders | open_so_invoices
            # If an order does not have original_request_date, it will be ignored in sorting,
            # keep them appended after sorted ones
            sorted_by_date = saleorders.filtered(
                lambda l: l.original_request_date
            ).sorted("original_request_date")
            unsorted = saleorders - sorted_by_date
            sorted_orders_asc = sorted_by_date | unsorted

            # Simulate credit usage across sorted orders and record hold flags
            counter_total = 0.0
            for order in sorted_orders_asc:
                if order not in paid_so_invoices:
                    counter_total += order.amount_total or 0.0

                credit_hold_flag = counter_total > (
                    order.partner_id.credit_limit or 0.0
                )

                # Override / already paid exceptions
                if order.override_credit_limit_hold:
                    credit_hold_flag = False
                if order in paid_so_invoices:
                    credit_hold_flag = False

                order_hold_map[order.id] = credit_hold_flag

        # Finally, assign computed values to the orders we were asked to compute (self)
        for order in self:
            order.credit_hold = bool(order_hold_map.get(order.id, False))

    @api.depends(
        "amount_total",
        "invoice_status",
    )
    def _compute_uninvoiced_balance(self):
        """
        Compute the uninvoiced balance:
        - If not fully invoiced, equal to order total.
        - Otherwise zero.
        """
        for order in self:
            order.uninvoiced_balance = (
                order.amount_total if order.invoice_status != "invoiced" else 0
            )

    @api.depends(
        "company_id",
        "partner_id",
        "amount_total",
    )
    def _compute_partner_credit_warning(self):
        """
        Placeholder: Compute partner credit warning message for SO.
        Currently sets an empty string (extend as needed).
        """
        for order in self:
            order.partner_credit_warning = ""
