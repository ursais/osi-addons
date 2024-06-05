from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    vw_division = fields.Char(string="Division")
    vw_applicant_name = fields.Char(string="Applicant Name")
    vw_file = fields.Char(string="File")
    vw_applicant_email = fields.Char(string="Applicant email")
    vw_reference = fields.Char(string="Reference")
    vw_flag = fields.Boolean(compute="_compute_vw_flag", store=True)

    @api.depends("partner_id.l10n_mx_edi_addenda")
    def _compute_flag(self):
        for record in self:
            record.vw_flag = (
                record.partner_id.l10n_mx_edi_addenda_name == "Addenda Volkswagen"
            )
