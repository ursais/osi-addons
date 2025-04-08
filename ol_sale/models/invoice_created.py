# Import Python libs
import logging

# Import Odoo libs
from odoo import models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    """
    An extension of the base Picking class automatically creates invoices on transfer

    As part of our workflow we want invoices to be created automatically for outgoing and incoming
    shipments to reduce the overhead for finance and fulfillment. The stock picking already has a
    reference to its purchase or sale, so use the existing invoice creation functions to create an
    invoice after transferring stock.
    """

    _inherit = 'stock.picking'

    # TODO: NC : ls_auto_invoice module not migrated
    # def auto_invoice_action_done(self, invoices):
    #     """
    #     Hook into the auto_invoice action_done method to trigger the Sale Order Account Manager email sending
    #     @param invoices: `account.move`
    #     @return:
    #     """
    #     self.ensure_one()
    #
    #     super(StockPicking, self).auto_invoice_action_done(invoices)
    #
    #     if not self.sale_id or not invoices:
    #         # We only want to continue if the Stock Picking has a related Sale Order and Invoices were created
    #         return False
    #
    #     email_template = self.env.ref('ol_sale.invoice_created_email_template')
    #     email_template.with_context(
    #         email_template_data={'invoices': invoices}, immediate_email_sending=True
    #     ).send_mail(res_id=self.sale_id.id, force_send=True)
    #     _logger.info(
    #         f"Email sent to Account Manager {self.sale_id.account_manager_id} for Invoice creation ({invoices}) for Sale Order ({self.sale_id})"
    #     )

    def _action_done(self):
        # Do the transfer
        res = super()._action_done()

        for picking in self:
            invoices = picking.sale_id.invoice_ids or self.env['account.move']
            if not picking.sale_id or not invoices:
                # We only want to continue if the Stock Picking has a related Sale Order and Invoices were created
                return res

            email_template = self.env.ref('ol_sale.invoice_created_email_template')
            local_context = dict(self.env.context.copy())
            local_context.update({
                "email_template_data": {'invoices': invoices},
                "immediate_email_sending": True
            })
            email_template.with_context(**local_context).send_mail(res_id=picking.sale_id.id, force_send=True)
            invoice_names = ", ".join(invoices.mapped('name')) or ""
            _logger.info(
                f"Email sent to Account Manager {picking.sale_id.account_manager_id.name} for Invoice creation ({invoice_names}) for Sale Order ({picking.sale_id.name})"
            )

        return res
