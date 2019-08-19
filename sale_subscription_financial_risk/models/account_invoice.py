from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    run_suspension_check = fields.Boolean(default=False)

    # override the write method to update run_suspension
    # invoice stage == 'paid'
    @api.multi
    def write(self, vals):
        if 'state' in vals:
            if vals['state'] == 'paid':
                vals.update({'run_suspension_check': True})
                _logger.info('Jacob updated run_susp_check to True')
            else:
                vals.update({'run_suspension_check': False})
                _logger.info('Jacob updated run_susp_check to False')
        return super(AccountInvoice, self).write(vals)

    # after checking, need to write bool back to False
