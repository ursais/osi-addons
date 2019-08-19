from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    run_suspension = fields.Booleans(default=False)

    # override the write method to update run_suspension
    # invoice stage == 'paid'
    def write(self, vals):
        res = super().write(vals)
        if 'stage_id' in vals:
            if vals['stage_id'] == 'paid':
                self.run_suspension = True
            else:
                self.run_suspension = False
        return res
