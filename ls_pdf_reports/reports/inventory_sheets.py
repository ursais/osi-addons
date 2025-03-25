# Import Odoo libs
from odoo import api, models


class ReportInventorySheets(models.AbstractModel):
    _name = 'report.ls_pdf_reports.report_inventory_sheets'
    _description = 'Sheet for Physical Inventory'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Hook into render to set company specific format for the report"""

        # Get the module/report name from the class name
        report = self.env['ir.actions.report']._get_report_from_name(self._name.replace('report.', ''))

        inventories = self.env[report.model].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'data': data,
            'docs': inventories,
        }
