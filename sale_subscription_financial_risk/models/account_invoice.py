from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    # Bool which determines if we need to execute the financial risk check
    # This is set True only once during the write action when payment is rec'd
    run_suspension_check = fields.Boolean(default=False)

    @api.multi
    def write(self, vals):
        # If we are writing to 'state' to value 'paid', run the suspend check
        if 'state' in vals:
            if vals['state'] == 'paid':
                vals.update({'run_suspension_check': True})
                _logger.info('Jacob updated run_susp_check to True')
        # If we aren't writing to 'state' in this call, maintain 'false'
        else:
            vals.update({'run_suspension_check': False})
            _logger.info('Jacob updated run_susp_check to False')

        return super(AccountInvoice, self).write(vals)
