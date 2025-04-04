# Import Odoo libs
from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    """Inherit Account Move for field/method changes."""

    _inherit = "account.move"

    # METHODS ######

    def unlink(self):
        """
        Restrict deletion of account.move to only the system user
        and users with the special permission.
        Users should cancel account moves instead of deleting to adhere
        to Onlogic Accounting policy.
        """
        for move in self:
            # Allow deletion if the user is the system user to be safe
            # and not impact system operations
            if self.env.uid == 1:
                continue

            # Restrict deletion
            if not self.env.user.has_group("ol_account.group_account_move_delete"):
                raise UserError(
                    _(
                        "You are not allowed to delete account moves. "
                        "Please cancel them instead."
                    )
                )
            if move.state != "draft":
                raise UserError(
                    _(
                        "Only draft account moves can be deleted. "
                        "For posted moves, cancel them instead."
                    )
                )
        return super(AccountMove, self).unlink()

    def _auto_reconcile_deposits(self):
        """
        Automatically reconciles downpayment deposits with their corresponding invoices.
        - Filters invoices of type 'out_invoice'.
        - Identifies related sale orders.
        - Checks for unpaid downpayment invoices.
        - Matches and reconciles downpayment journal items with corresponding invoices.
        """
        for move in self.filtered(lambda m: m.move_type == "out_invoice"):
            so = self.env["sale.order"].search(
                [("invoice_ids", "in", [move.id])], limit=1
            )
            if not so:
                continue

            downpayment_moves = so.invoice_ids.filtered(
                lambda inv: inv.move_type == "out_invoice"
                and inv.payment_state != "paid"
                and inv.id != move.id
            )

            if not downpayment_moves:
                continue

            downpayment_lines = move.line_ids.filtered(lambda line: line.is_downpayment)

            for dp_move in downpayment_moves:
                dp_journal_items = dp_move.line_ids.filtered(
                    lambda line: line.is_downpayment and not line.reconciled
                )

                for dp_line in downpayment_lines:
                    matching_lines = dp_journal_items.filtered(
                        lambda line: line.balance == -dp_line.balance
                        and not line.reconciled
                    )

                    if matching_lines:
                        (matching_lines | dp_line).reconcile()

    def action_post(self):
        result = super().action_post()
        self._auto_reconcile_deposits()
        return result

    def action_invoice_print(self):
        """
        Override original invoice template
        """
        self.ensure_one()
        self.is_move_sent = True
        return self.env.ref("ol_account.action_generic_invoice_report").report_action(
            self
        )

    def get_report_invoice_data(self):
        data = {}
        for invoice in self:
            data[invoice.id] = {}
            order_data = False

            if invoice.line_ids.sale_line_ids:
                order_data = invoice.get_invoice_report_data_by_sale_order_lines()

            data[invoice.id]["sale_order"] = order_data

        return data

    def get_invoice_report_data_by_sale_order_lines(self):

        order_data = {
            "product_lines": [],
        }

        product_lines = self.env["sale.order.line"]

        for invoice_line in self.invoice_line_ids:
            for sale_order_line in invoice_line.sale_line_ids:

                if sale_order_line.is_delivery:
                    continue

                product_lines |= sale_order_line

                # TODO: NC : "sale_order_line.quote_config_id" Field not found
                quote_config = sorted_quote_lines = False
                # quote_config = sale_order_line.quote_config_id or False
                #
                # if quote_config:
                #     quote_lines = quote_config.quote_config_line_ids.filtered(
                #         lambda l: l.description_type != 'hide'
                #     )
                #     sorted_quote_lines = quote_lines.sorted(key=lambda q: q.product_id.sequence)
                # else:
                #     sorted_quote_lines = False

                order_line_data = {
                    "invoice_line": invoice_line,
                    "order_line": sale_order_line,
                    "quote_config": quote_config,
                    "quote_lines": sorted_quote_lines,
                }

                order_data["product_lines"].append(order_line_data)

        # Set the shipping lines
        shipping_lines = self.mapped("invoice_line_ids.sale_line_ids").filtered(
            lambda l: l.is_delivery
        )

        order_data["shipping_lines"] = shipping_lines
        order_data["product_subtotal_amount"] = sum(
            product_lines.mapped("price_subtotal")
        )
        order_data["shipping_subtotal_amount"] = sum(
            shipping_lines.mapped("price_subtotal")
        )

        return order_data

    def get_invoice_report_data(self):

        for invoice in self:

            filtered_invoice = invoice
            filtered_invoice_data = {
                "sum_amount": invoice.amount_total,
                "out_invoice_amount": None,
                "out_refund_amount": None,
                "payment_received_amount": (
                    invoice.amount_total - invoice.amount_residual
                ),
                "residual_amount": invoice.amount_residual,
                "type": invoice.get_report_title(),
            }

        res = {"invoice": filtered_invoice, "invoice_data": filtered_invoice_data}

        return res

    def get_report_title(self):
        """Return the report title defined by marketing"""

        if self.move_type == "out_refund":
            return "Refund"

        return "Invoice"

    # END ##########
