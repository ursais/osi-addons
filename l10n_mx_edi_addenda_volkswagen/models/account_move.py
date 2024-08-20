from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    vw_division = fields.Char(string="VW Division")
    vw_applicant_name = fields.Char(string="VW Applicant Name")
    vw_applicant_email = fields.Char(string="VW Applicant email")
    vw_flag = fields.Boolean(compute="_compute_vw_flag", store=True)

    @api.depends("partner_id.l10n_mx_edi_addenda")
    def _compute_vw_flag(self):
        for record in self:
            record.vw_flag = (
                record.partner_id.l10n_mx_edi_addenda_name == "Addenda Volkswagen"
            )
