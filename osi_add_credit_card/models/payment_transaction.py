# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.addons.payment_authorize.models.authorize_request import AuthorizeAPI


class TxAuthorize(models.Model):
    _inherit = 'payment.transaction'

    @api.multi
    def authorize_s2s_do_transaction(self, **data):
        # Check for payment type outbound and call refund instead of regular
        if all (k in self._context for k in ("active_model","type")) and\
            self._context.get('active_model') == 'account.invoice' and\
            self._context.get('type') == 'out_refund':
            self.ensure_one()
            # Get the origin invoice related to refund invoice
            refund_invoice = self.env['account.invoice'].browse([
                self._context.get('active_id')])
            origin_str = refund_invoice.origin
            origin_invoice = self.env['account.invoice'].search([
                ('number','=',refund_invoice.origin)], limit=1)
            if not origin_invoice:
                raise UserError(
                    "Not valid source invoice reference: %s" % (
                        refund_invoice.origin)
                    )
            # Get the acquirer_reference from source origin of refund and 
            # consider the first payment as a reference
            acquirer_reference = ''
            for payment in origin_invoice.payment_ids.sorted():
                acquirer_reference = payment.payment_transaction_id and\
                    payment.payment_transaction_id.acquirer_reference or ''
                break
            if not acquirer_reference:
                raise UserError(
                    "There is not payment entry for origin invoice: %s" % (
                        origin_invoice.name)
                    )
            transaction = AuthorizeAPI(self.acquirer_id)
            res = transaction.credit(self.payment_token_id, self.amount, acquirer_reference)
            return self._authorize_s2s_validate_tree(res)
        else:
            return super(TxAuthorize, self).authorize_s2s_do_transaction(**data)
