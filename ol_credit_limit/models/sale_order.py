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
        query = """
            SELECT id
            FROM sale_order
            WHERE partner_id IN %s
            AND invoice_status != 'invoiced'
            AND state not in ('cancel','draft')
        """
        self.env.cr.execute(
            query, (tuple(partner_ids.ids),)
        )  # Ensure tuple format for SQL IN clause
        so_list = [so[0] for so in self.env.cr.fetchall()]

        return so_obj.browse(so_list)

    @api.depends(
        "partner_id.remaining_credit",
        "partner_id.open_so_balance",
        "override_credit_limit_hold",
    )
    def _compute_credit_hold(self):
        """
        Compute credit hold for Sale Orders.

        Steps:
          1. Gather all open SOs for the partner (and its children).
          2. Include invoices linked to SO lines (paid vs unpaid).
          3. Iterate through orders in ascending request date.
          4. Accumulate totals until exceeding partner credit limit.
          5. Mark orders as credit hold if over the limit, unless:
             - Override flag is set, or
             - Order is already fully paid.
        """
        # Optimization: Avoid expensive operations when not needed
        # If the partner doesn't have any rollup or children, we can optimize
        if not self.partner_id.rollup_partner_ids and not self.partner_id.child_ids:
            # For simple partners, we can avoid complex filtering
            self.credit_hold = False
            return

        open_saleorders = self._get_open_sale_order(self.mapped("partner_id"))

        self.credit_hold = False

        # Collect all children of the customer
        all_child = (
            self.env["res.partner"]
            .with_context(active_test=False)
            .search([("id", "child_of", self.partner_id.ids)])
        )

        # Unpaid invoices (still outstanding)
        not_paid_invoices = self.env["account.move"].search(
            [
                ("move_type", "=", "out_invoice"),
                ("partner_id", "in", all_child.ids),
                ("state", "!=", "cancel"),
            ]
        )
        open_so_invoices = not_paid_invoices.mapped("line_ids.sale_line_ids.order_id")

        # Paid / in payment invoices
        paid_invoices = self.env["account.move"].search(
            [
                ("move_type", "=", "out_invoice"),
                ("partner_id", "in", all_child.ids),
                ("state", "!=", "cancel"),
                ("payment_state", "in", ["in_payment", "paid"]),
            ]
        )
        paid_so_invoices = paid_invoices.mapped("line_ids.sale_line_ids.order_id")

        # Combine orders: open SOs + those linked to unpaid invoices
        saleorders = open_saleorders + open_so_invoices

        # Sort by requested delivery date to decide which orders get blocked first
        sorted_orders_asc = (
            self.env["sale.order"]
            .browse(saleorders.ids)
            .filtered(lambda l: l.original_request_date)
            .sorted("original_request_date")
        )

        # Running counter to simulate credit usage across order
        counter_total = 0
        for order in sorted_orders_asc:
            if order.id not in paid_so_invoices.ids:
                counter_total += order.amount_total
            credit_hold = False
            if counter_total > order.partner_id.credit_limit:
                credit_hold = True
            if order.override_credit_limit_hold:
                credit_hold = False
            if order.id in paid_so_invoices.ids:
                credit_hold = False
            order.credit_hold = credit_hold

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
