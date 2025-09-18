# Import Odoo libs
from odoo import _, api, fields, models


class SaleOrder(models.Model):
    """
    Inherit Sale Order Object to add Credit Limit.
    """

    _inherit = "sale.order"

    # COLUMNS #####

    credit_hold = fields.Boolean(
        "Credit Hold",
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
        print("////",so_list)
        return so_obj.browse(so_list)

    @api.depends(
        "partner_id.remaining_credit",
        "partner_id.open_so_balance",
        "override_credit_limit_hold",
    )
    def _compute_credit_hold(self):
        open_saleorders = self._get_open_sale_order(self.mapped("partner_id"))
        print("////open_saleorders/////",open_saleorders)
        counter_total = 0
        self.   credit_hold = False
        all_child = (
            self.env["res.partner"]
            .with_context(active_test=False)
            .search([("id", "child_of", self.partner_id.ids)])
        )
        not_paid_invoices = self.env["account.move"].search(
            [
                ("move_type", "=", "out_invoice"),
                ("partner_id", "in", all_child.ids),
                ("state", "!=", "cancel"),
            ]
        )
        open_so_invoices = not_paid_invoices.mapped("line_ids.sale_line_ids.order_id")
        paid_invoices = self.env["account.move"].search(
            [
                ("move_type", "=", "out_invoice"),
                ("partner_id", "in", all_child.ids),
                ("state", "!=", "cancel"),
                ("payment_state", "in", ["in_payment", "paid"]),
            ]
        )
        print(all_child,"///////open_so_invoices////////",open_so_invoices)
        paid_so_invoices = paid_invoices.mapped("line_ids.sale_line_ids.order_id")
        print(paid_invoices,"///paid_so_invoices///",paid_so_invoices)
        saleorders = open_saleorders + open_so_invoices
        sorted_orders_asc = (
            self.env["sale.order"]
            .browse(saleorders.ids)
            .filtered(lambda l: l.original_request_date)
            .sorted("original_request_date")
        )
        counter_total = 0
        for order in sorted_orders_asc:
            print("///////order/",order)
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

        # for order in self:
        #     if not sorted_orders_asc:


    @api.depends("amount_total", "invoice_status")
    def _compute_uninvoiced_balance(self):
        for order in self:
            order.uninvoiced_balance = (
                order.amount_total if order.invoice_status != "invoiced" else 0
            )

    @api.depends("company_id", "partner_id", "amount_total")
    def _compute_partner_credit_warning(self):
        for order in self:
            order.partner_credit_warning = ""
