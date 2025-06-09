# Import Odoo libs
from odoo import _, api, fields, models
import logging

_logger = logging.getLogger(__name__)


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
            AND state != 'cancel'
        """
        self.env.cr.execute(
            query, (tuple(partner_ids.ids),)
        )  # Ensure tuple format for SQL IN clause
        so_list = [so[0] for so in self.env.cr.fetchall()]
        return so_obj.browse(so_list)

    def _get_sale_order_id(self,invoices):
        sols = []
        sale_orders = self.env['sale.order']
        query = """SELECT id FROM account_move_line WHERE move_id IN %s"""
        self.env.cr.execute(query, (tuple(invoices),))  # Note the trailing comma
        datas = self.env.cr.fetchall()
        not_paid_amls = [row[0] for row in datas]
        if not_paid_amls:
            query = """SELECT order_line_id from sale_order_line_invoice_rel where invoice_line_id in %s; """
            self.env.cr.execute(query, (tuple(not_paid_amls),))  # Note the trailing comma
            datas = self.env.cr.fetchall()
            sols = [row[0] for row in datas]
        if sols:
            query = """select DISTINCT order_id from sale_order_line where id in %s;"""
            self.env.cr.execute(query, (tuple(sols),))  # Note the trailing comma
            datas = self.env.cr.fetchall()
            order_ids = [row[0] for row in datas]
            sale_orders = self.env['sale.order'].browse(order_ids)
        return sale_orders


    @api.depends(
        "partner_id.remaining_credit",
        "partner_id.open_so_balance",
        "override_credit_limit_hold",
    )
    def _compute_credit_hold(self):
        for sale in self:
            open_saleorders = self._get_open_sale_order(sale.mapped("partner_id"))
            _logger.info("_compute_credit_hold %s", self.mapped("partner_id"))
            open_so_invoices = self.env['sale.order']
            paid_so_invoices = self.env['sale.order']
            cr = self.env.cr
            counter_total = 0
            credit_hold = False
            all_child = (
                self.env["res.partner"]
                .with_context(active_test=False)
                .search([("id", "child_of", self.partner_id.ids)])
            )
            query = """
                SELECT id
                FROM account_move
                WHERE move_type = 'out_invoice'
                AND partner_id IN %s
                AND state != 'cancel'
            """
            cr.execute(query, (tuple(all_child.ids),))  # Wrap in tuple
            datas = cr.fetchall()
            not_paid_invoices = [row[0] for row in datas]

            not_paid_amls = False
            sols = False

            if not_paid_invoices:
                open_so_invoices = self._get_sale_order_id(not_paid_invoices)
            query = """
                SELECT id
                FROM account_move
                WHERE move_type = 'out_invoice'
                AND state != 'cancel'
                AND partner_id IN %s
                AND payment_state IN %s
            """
            move_ids = tuple(not_paid_invoices) or (0,)
            partns = tuple(all_child.ids)
            payment_states = ('in_payment', 'paid')
            cr.execute(query, (partns, payment_states))
            datas = cr.fetchall()
            paid_invoices = [row[0] for row in datas]
            if paid_invoices:
                paid_so_invoices = self._get_sale_order_id(paid_invoices)

            saleorders = open_saleorders + open_so_invoices
            sorted_orders_asc = (
                self.env["sale.order"]
                .browse(saleorders.ids)
                .filtered(lambda l: l.original_request_date)
                .sorted("original_request_date")
            )
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


            # not_paid_invoices = self.env["account.move"].search(
            #     [
            #         ("move_type", "=", "out_invoice"),
            #         ("partner_id", "in", all_child.ids),
            #         ("state", "!=", "cancel"),
            #     ]
            # )
            # open_so_invoices = not_paid_invoices.mapped("line_ids.sale_line_ids.order_id")
            # paid_invoices = self.env["account.move"].search(
            #     [
            #         ("move_type", "=", "out_invoice"),
            #         ("partner_id", "in", all_child.ids),
            #         ("state", "!=", "cancel"),
            #         ("payment_state", "in", ["in_payment", "paid"]),
            #     ]
            # )
            # paid_so_invoices = paid_invoices.mapped("line_ids.sale_line_ids.order_id")
            # saleorders = open_saleorders + open_so_invoices
            # sorted_orders_asc = (
            #     self.env["sale.order"]
            #     .browse(saleorders.ids)
            #     .filtered(lambda l: l.original_request_date)
            #     .sorted("original_request_date")
            # )
            # counter_total = 0
            # for order in sorted_orders_asc:
            #     if order.id not in paid_so_invoices.ids:
            #         counter_total += order.amount_total
            #     credit_hold = False
            #     if counter_total > order.partner_id.credit_limit:
            #         credit_hold = True
            #     if order.override_credit_limit_hold:
            #         credit_hold = False
            #     if order.id in paid_so_invoices.ids:
            #         credit_hold = False
            #     order.credit_hold = credit_hold

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
