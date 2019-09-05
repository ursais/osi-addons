# Copyright (C) 2019 Amplex
# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    # Bool which determines if we need to execute the financial risk check
    # This is set True only once during the write action when payment is rec'd
    run_suspension_check = fields.Boolean(default=False)

    @api.multi
    def write(self, vals):
        # If we aren't writing to 'state' in this call, maintain 'false'
        run_suspension_check = False
        # If we are writing to 'state' to value 'paid', run the suspend check
        if vals.get('state', False) == 'paid':
            run_suspension_check = True
        # update the variable
        vals.update({'run_suspension_check': run_suspension_check})

        return super(AccountInvoice, self).write(vals)
