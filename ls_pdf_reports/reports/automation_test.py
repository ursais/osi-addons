# Import Odoo libs
from odoo import api, models


class ReportProductionAutomationTest(models.AbstractModel):
    _name = 'report.ls_pdf_reports.report_mo_automation_test_results'
    _description = 'Automation Test Results for MOs'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Hook into render to set company specific format for the report"""

        # Get the module/report name from the class name
        report = self.env['ir.actions.report']._get_report_from_name(self._name.replace('report.', ''))

        production_ids = self.env[report.model].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'data': data,
            'docs': production_ids,
        }
