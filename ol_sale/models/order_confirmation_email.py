# Import Python libs
import logging

# Import Odoo libs
from odoo import fields, models, api, _, registry

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """
    Confirmation email related functionality
    """

    _inherit = 'sale.order'

    to_send_confirmation_email = fields.Boolean(string='Send confirmation email', default=True, copy=False)

    def _send_order_confirmation_mail(self):
        """
        We don't want core to send anything, we handle the order confirmation email ourselves
        """
        return


    def toggle_confirmation_email(self):
        """
        Toggle whether to send the email or not
        """

        for order in self:
            order.to_send_confirmation_email = not order.to_send_confirmation_email

    def send_confirmation_email(self):
        """
        Send a Sale Order confirmation email
        """
        self.ensure_one()

        if not self.to_send_confirmation_email:
            return

        # Create and send the email based on the confirmation template immediately
        self.env.ref('ol_sale.order_confirmation_email_template').send_email_with_terms_and_conditions(
            self.company_id, self.id
        )

    def _pre_confirm_check_actions(self):
        """
        Hook into this action to notify the user about the new order
        """
        self.ensure_one()
        self.send_confirmation_email()
        res = super(SaleOrder, self)._pre_confirm_check_actions()

        # Make sure to disable future email sending
        # We do this after `_pre_confirm_actions` run as
        # other triggers could depend on `to_send_confirmation_email` being True
        # (could be overwritten manually)
        self.to_send_confirmation_email = False

        return res

    def _pre_confirm_actions(self):
        """
        Hook into this action to notify the user about the new order
        """
        self.ensure_one()
        self.send_confirmation_email()
        res = super(SaleOrder, self)._pre_confirm_actions()

        # Make sure to disable future email sending
        # We do this after `_pre_confirm_actions` run as
        # other triggers could depend on `to_send_confirmation_email` being True
        # (could be overwritten manually)
        self.to_send_confirmation_email = False

        return res

    def action_open_forward_confirmation_email_wizard(self):
        """Open forward confirmation wizard"""
        self.ensure_one()

        return self.env.ref('ol_sale.action_forward_confirmation_email_wizard').read()[0]


    def action_confirm(self):
        res = super().action_confirm()
        self.send_confirmation_email()
        return res
