# Import Odoo libs
from odoo import api, models


class ReportGenericInvoice(models.AbstractModel):
    _name = 'report.ol_account.report_generic_invoice'
    _description = 'Generic Invoice Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Hook into render to set company specific format for the report"""

        # Get the module/report name from the class name
        report = self.env['ir.actions.report']._get_report_from_name(self._name.replace('report.', ''))

        account_moves = self.env[report.model].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'data': data,
            'docs': account_moves,
            'onlogic_data': account_moves.get_report_invoice_data(),
        }
