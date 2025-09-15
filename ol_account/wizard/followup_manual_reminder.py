from odoo import api, fields, models, Command


class FollowupManualReminder(models.TransientModel):
    _inherit = 'account_followup.manual_reminder'


    @api.depends('template_id')
    def _compute_email_recipient_ids(self):
        for wizard in self:
            partner = wizard.partner_id
            template = wizard.template_id
            wizard.email_recipient_ids = partner._get_all_followup_contacts()