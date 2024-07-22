from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    audi_business_unit = fields.Char(string="Business Unit")
    audi_applicant_email = fields.Char(string="Applicant email")
    audi_flag = fields.Boolean(compute="_compute_audi_flag", store=True)
    audi_tax_code = fields.Char(string="Tax Code")
    audi_fiscal_document_type = fields.Char(string="Fiscal Document Type")
    audi_document_type = fields.Char(string="Document Type")

    @api.depends("partner_id.l10n_mx_edi_addenda")
    def _compute_audi_flag(self):
        for record in self:
            record.audi_flag = (
                record.partner_id.l10n_mx_edi_addenda_name == "Addenda Audi"
            )
