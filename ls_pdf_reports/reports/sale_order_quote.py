# Import Odoo libs
from odoo import api, models


class ReportSaleOrderQuote(models.AbstractModel):
    _name = 'report.ls_pdf_reports.report_sale_order_quote'
    _description = 'Sale Order Quote'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Hook into render to set company specific format for the report"""

        # Get the module/report name from the class name
        report = self.env['ir.actions.report']._get_report_from_name(self._name.replace('report.', ''))

        sale_orders = self.env[report.model].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'data': data,
            'docs': sale_orders,
            'onlogic_data': sale_orders.get_quote_report_data(),
        }
