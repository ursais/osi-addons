from odoo import api, fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    audi_business_unit = fields.Char(string="Business Unit")
    audi_applicant_email = fields.Char(string="Applicant email")
    audi_flag = fields.Boolean(compute="_compute_flag")

    @api.depends("partner_id.l10n_mx_edi_addenda")
    def _compute_flag(self):
        for record in self:
            record.audi_flag = (
                record.partner_id.l10n_mx_edi_addenda_name == "Addenda Audi"
            )
