# Import Odoo libs
from odoo import api, models


class ReportPackingSlip(models.AbstractModel):
    _name = 'report.ls_pdf_reports.report_packing_slip'
    _description = 'Packing Slip Report'

    @api.model
    def _get_report_values(self, docids, data=None):

        # Get the module/report name from the class name
        report = self.env['ir.actions.report']._get_report_from_name(self._name.replace('report.', ''))

        stock_pickings = self.env[report.model].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'data': data,
            'docs': stock_pickings,
        }
