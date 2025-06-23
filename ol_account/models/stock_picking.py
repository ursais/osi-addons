# Import Odoo libs
from odoo import fields, models


class StockPicking(models.Model):
    """
    Inherit the stock picking to add auto invoicing functionality.
    """

    _inherit = "stock.picking"

    # METHODS ######

    def _action_done(self):
        """
        Inherit the validate method that runs on delivery orders to
        auto create/post the invoice if related to a sale order.
        """
        res = super()._action_done()

        config = self.env["ir.config_parameter"].sudo()

        # Get General Settings
        auto_create_invoice = (
            config.get_param("ol_account.auto_create_invoice_delivery_validate")
            == "True"
        )
        auto_post_invoice = (
            config.get_param("ol_account.auto_post_invoice_delivery_validate") == "True"
        )
        auto_create_bill = (
            config.get_param("ol_account.auto_create_bill_receipt_validate") == "True"
        )
        auto_post_bill = (
            config.get_param("ol_account.auto_post_bill_receipt_validate") == "True"
        )

        for picking in self:
            # Ensure this picking is a delivery order and linked to a Sale Order
            if (
                picking.picking_type_id.code == "outgoing"
                and picking.sale_id
                and auto_create_invoice
            ):
                if (
                    any(
                        rec.product_id.invoice_policy == "delivery"
                        for rec in self.move_ids
                    )
                    or not self.sale_id.invoice_ids
                ):
                    # Call the _create_invoices function on the associated sale
                    # to create the invoice ('final' being true will include down payments)
                    invoice_created = self.sale_id._create_invoices(
                        self.sale_id,
                        final=True,
                    )

                    # Post the created invoice
                    if (
                        invoice_created
                        and invoice_created.state == "draft"
                        and auto_post_invoice
                    ):
                        # If auto posting is enabled then post the invoice.
                        invoice_created.action_post()

            # Ensure this picking is a receipt order and linked to a Sale Order
            if (
                picking.picking_type_id.code == "incoming"
                and picking.purchase_id
                and auto_create_bill
            ):
                if (
                    any(
                        rec.product_id.purchase_method == "receive"
                        for rec in self.move_ids
                    )
                    or not self.purchase_id.invoice_ids
                ):
                    # Call the action_create_invoices function on the associated po
                    picking.purchase_id.action_create_invoice()

                    # Find the newly created invoice
                    bill_created = picking.purchase_id.invoice_ids.sorted(
                        "id", reverse=True
                    )[0]

                    # Post the created bill
                    if (
                        bill_created
                        and bill_created.state == "draft"
                        and auto_post_bill
                    ):
                        # If invoice date isn't set
                        if not bill_created.invoice_date:
                            bill_created.invoice_date = fields.Date.today()

                        # If auto posting is enabled then post the bill.
                        bill_created.action_post()

        return res

    # END ##########
