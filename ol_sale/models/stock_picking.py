# Import Odoo libs
from odoo import api, fields, models


class StockPicking(models.Model):
    """Add new field to Pickings."""

    _inherit = "stock.picking"

    # COLUMNS #####

    to_send_customer_shipment = fields.Boolean(
        string="Send Shipment Email",
        tracking=True,
    )

    # END #########

    def button_validate(self):
        """
        Prevent transfer if any holds on any sale orders
        """

        res = super(StockPicking, self).button_validate()

        # Send an email later for delivery orders
        self.to_send_customer_shipment = True

        return res

    def get_shipment_email_search_domain(self):
        """
        Domain to search for invoices to send out.
        """

        return [
            ("company_id", "=", self.env.company.id),
            ("to_send_customer_shipment", "=", True),
            ("picking_type_id.code", "=", "outgoing"),
            ("state", "=", "done"),
        ]

    @api.model
    def send_customer_emails(self):
        """Send emails for all shipments flagged to send"""
        domain = self.get_shipment_email_search_domain()
        picking_ids = self.search(domain)
        shipment_template = self.env.ref("ol_sale.customer_shipment_email_template")

        failed_picking_ids = self.env["stock.picking"]
        for picking_id in picking_ids:
            if not picking_id.sale_id:
                picking_id.to_send_customer_shipment = False
                continue
            try:
                shipment_template.send_mail(picking_id.id)
                picking_id.to_send_customer_shipment = False
            except Exception:
                failed_picking_ids |= picking_id
        if failed_picking_ids:
            for failed_picking_id in failed_picking_ids:
                if failed_picking_id.sale_id:
                    failed_picking_id.sale_id.message_post(
                        body=f"Shipment email failed to send for shipment: {failed_picking_id.name}. "
                        f"Contact IT Support.",
                        subtype="ol_base.it_support_message_subtype",
                    )
                else:
                    failed_picking_id.message_post(
                        body="Shipment email failed to send! Contact IT Support.",
                        subtype="ol_base.it_support_message_subtype",
                    )

    def _action_done(self):
        """
        As part of our workflow we want invoices to be created automatically for outgoing
        shipments to reduce the overhead for finance. The stock picking already has a
        reference to its purchase or sale, ol_account will create the invoice if enabled
        in settings so this should trigger an email when that happens.
        """
        # Do the transfer
        res = super()._action_done()

        for picking in self:
            invoices = picking.sale_id.invoice_ids or self.env["account.move"]
            if not picking.sale_id or not invoices:
                # We only want to continue if the Stock Picking has a related Sale Order and Invoices were created
                continue

            email_template = self.env.ref("ol_sale.invoice_created_email_template")
            local_context = dict(self.env.context.copy())
            local_context.update(
                {
                    "email_template_data": {"invoices": invoices},
                    "immediate_email_sending": True,
                }
            )
            email_template.with_context(**local_context).send_mail(
                res_id=picking.sale_id.id, force_send=True
            )

        return res
