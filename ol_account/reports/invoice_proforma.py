# Import Odoo libs
from odoo import api, models


class ReportProformaInvoice(models.AbstractModel):
    _name = "report.ol_account.report_proforma_invoice"
    _description = "Pro-forma Invoice Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        """Hook into render to set company specific format for the report"""

        # Get the module/report name from the class name
        report = self.env["ir.actions.report"]._get_report_from_name(
            self._name.replace("report.", "")
        )

        sale_order = self.env[report.model].browse(docids)

        return {
            "doc_ids": docids,
            "doc_model": report.model,
            "data": data,
            "docs": sale_order,
            "onlogic_data": sale_order.get_quote_report_data(),
        }
