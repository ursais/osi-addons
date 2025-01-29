# Import Odoo libs
from odoo import models


class StockPicking(models.Model):
    """
    Inherit the stock picking to add auto invoicing functionality.
    """

    _inherit = "stock.picking"

    # METHODS ######

    def button_validate(self):
        """
        Inherit the validate method that runs on delivery orders to
        auto create/post the invoice if related to a sale order.
        """
        res = super().button_validate()

        # Ensure this picking is a delivery order and linked to a Sale Order
        if not self.sale_id or self.picking_type_id.code != "outgoing":
            return res

        # Get settings
        auto_validate_invoice = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("ol_account.auto_create_invoice_delivery_validate")
        )
        auto_post_invoice = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("ol_account.auto_post_invoice_delivery_validate")
        )
        if auto_validate_invoice:
            if (
                any(
                    rec.product_id.invoice_policy == "delivery" for rec in self.move_ids
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
                if invoice_created and auto_post_invoice:
                    # If auto posting is enabled then post the invoice.
                    invoice_created.action_post()

        return res

    # END ##########
