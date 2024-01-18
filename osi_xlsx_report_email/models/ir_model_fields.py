from odoo import api, fields, models


class IRModelFields(models.Model):
    _inherit = 'ir.model.fields'

    xlsx_report_fields_ids = fields.Many2many(
        comodel_name="xlsx.report.email",
        relation="xlsx_report_email_ir_model_fields_report_fields_rel",
        column2="xlsx_report_email_report_field_id",
        column1="report_field_id",
        string='Report XLSX Reports'
    )

    xlsx_domain_fields_ids = fields.Many2many(
        comodel_name="xlsx.report.email",
        relation="xlsx_report_email_ir_model_fields_domain_fields_rel",
        column2="xlsx_report_email_domain_field_id",
        column1="domain_field_id",
        string='Domain XLSX Reports'
    )
