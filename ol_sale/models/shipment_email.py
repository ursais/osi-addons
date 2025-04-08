from odoo import models, api, fields, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # COLUMNS #####
    to_send_customer_shipment = fields.Boolean(string='Send Shipment Email', tracking=True)

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
            ('company_id', '=', self.env.company.id),
            ('to_send_customer_shipment', '=', True),
            ('picking_type_id.code', '=', 'outgoing'),
            ('state', '=', 'done'),
        ]

    @api.model
    def send_customer_emails(self):
        """Send emails for all shipments flagged to send"""
        domain = self.get_shipment_email_search_domain()
        picking_ids = self.search(domain)
        shipment_template = self.env.ref('ol_sale.customer_shipment_email_template')

        failed_picking_ids = self.env['stock.picking']
        for picking_id in picking_ids:
            if not picking_id.sale_id:
                _logger.warning(
                    f'Skipping shipment email for [{picking_id.name}] due to no linked Sale Order'
                )
                picking_id.to_send_customer_shipment = False
                continue
            _logger.info(
                'Sending shipment email for [{name}] '
                'Sale Order: [{sale}]'.format(name=picking_id.name, sale=picking_id.sale_id.name)
            )
            try:
                shipment_template.send_mail(picking_id.id)
                picking_id.to_send_customer_shipment = False
            except Exception:
                _logger.exception(
                    f"Failed to send Shipment email for: {picking_id.name} {picking_id} ({picking_id.sale_id or ''})"
                )
                failed_picking_ids |= picking_id
        if failed_picking_ids:
            _logger.error(f'Failed to send {len(failed_picking_ids)} shipment emails')
            for failed_picking_id in failed_picking_ids:
                if failed_picking_id.sale_id:
                    failed_picking_id.sale_id.message_post(
                        body=f'Shipment email failed to send for shipment: {failed_picking_id.name}. '
                        f'Contact IT Support.',
                        subtype='ol_base.it_support_message_subtype',
                    )
                else:
                    failed_picking_id.message_post(
                        body='Shipment email failed to send! Contact IT Support.',
                        subtype='ol_base.it_support_message_subtype',
                    )

    def get_email_recipients(self):
        """ Helper function to get all recipients of a shipment email """
        partner = self.partner_id
        if not partner:
            return
        contacts = partner
        if self.sale_id:
            contacts += self.sale_id.partner_id
        return contacts
        # emails = list(set(contacts.mapped('email')))
        # return u','.join(email.strip() for email in emails if email and email.strip())
