from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    run_suspension_check = fields.Boolean(default=False)

    # override the write method to update run_suspension
    # invoice stage == 'paid'
    @api.multi
    def write(self, vals):
        if 'stage_id' in vals:
            if vals['stage_id'] == 'paid':
                vals.update({'run_suspension_check': True})
            else:
                vals.update({'run_suspension_check': False})
        return super().write(vals)
