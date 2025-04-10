from odoo import models, api


class AccountMoveSend(models.TransientModel):
    _inherit = 'account.move.send'

    @api.model
    def _get_placeholder_mail_template_dynamic_attachments_data(self, move, mail_template):
        res = super(AccountMoveSend, self)._get_placeholder_mail_template_dynamic_attachments_data(move, mail_template)
        invoice_template = self.env.ref('ol_account.action_generic_invoice_report')
        if invoice_template:
            extra_mail_templates = mail_template.report_template_ids - invoice_template
            filename = move._get_invoice_report_filename()
            return [
                {
                    'id': f'placeholder_{extra_mail_template.name.lower()}_{filename}',
                    'name': f'{extra_mail_template.name.lower()}_{filename}',
                    'mimetype': 'application/pdf',
                    'placeholder': True,
                    'dynamic_report': extra_mail_template.report_name,
                } for extra_mail_template in extra_mail_templates
            ]
        return res

    @api.model
    def _prepare_invoice_pdf_report(self, invoice, invoice_data):
        res = super(AccountMoveSend, self)._prepare_invoice_pdf_report(invoice, invoice_data)
        content, _report_format = self.env['ir.actions.report']\
            .with_company(invoice.company_id)\
            .with_context(from_account_move_send=True)\
            ._render('ol_account.action_generic_invoice_report', invoice.ids)

        invoice_data['pdf_attachment_values'] = {
            'raw': content,
            'name': invoice._get_invoice_report_filename(),
            'mimetype': 'application/pdf',
            'res_model': invoice._name,
            'res_id': invoice.id,
            'res_field': 'invoice_pdf_report_file', # Binary field
        }
        return res
