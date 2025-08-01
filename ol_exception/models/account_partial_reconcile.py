# # Import Odoo libs
from odoo import api, models


class AccountPartialReconcile(models.Model):
    """Inherit account.partial.reconcile to trigger sale order exception checks
    whenever payments are reconciled or unreconciled on related invoices."""

    _inherit = "account.partial.reconcile"

    # METHODS ##########

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override batch create of partial reconciliations (payment reconciliations).

        After the reconciliation records are created, find all related customer invoices
        (including down payments) and trigger exception checks on linked sale orders.

        :param vals_list: list of dictionaries with values to create reconciliations
        :return: created recordset of partial reconciliations
        """
        # Call super to create the partial reconcile records as usual
        records = super().create(vals_list)

        # Map to all invoices related to the debit moves of the reconciliations
        invoices = records.mapped("debit_move_id.move_id").filtered(
            lambda m: m.move_type in ("out_invoice", "out_refund")
        )
        if invoices:
            # Find sale orders via origin (works for downpayments)
            origins = invoices.mapped("invoice_origin")
            sale_orders = self.env["sale.order"].search([("name", "in", origins)])
            if sale_orders:
                sale_orders.sale_check_exception()

        return records

    def unlink(self):
        """
        Override unlink to handle unreconciliation events.

        Before deleting reconciliation links, find related invoices and sale orders,
        then after unlinking trigger exception checks on those sale orders.

        :return: result of the unlink operation
        """
        # Find invoices related to the reconciliations being removed
        invoices = self.mapped("debit_move_id.move_id").filtered(
            lambda m: m.move_type in ("out_invoice", "out_refund")
        )
        sale_orders = self.env["sale.order"]
        if invoices:
            # Find sale orders by invoice origin
            origins = invoices.mapped("invoice_origin")
            sale_orders = self.env["sale.order"].search([("name", "in", origins)])

        # Call super to actually remove the reconciliation records
        result = super().unlink()

        if sale_orders:
            # After unlinking, trigger exception checks on sale orders again
            sale_orders.sale_check_exception()

        return result

    # END ##########
