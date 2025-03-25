# Import Odoo libs
from odoo import api, models
from odoo.exceptions import ValidationError


class ReportProformaInvoiceFromSo(models.AbstractModel):
    _name = 'report.ls_pdf_reports.report_proforma_invoice_from_so'
    _description = 'Pro-forma Invoice Report (from Sale Order)'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Hook into render to set company specific format for the report"""

        # Get the module/report name from the class name
        report = self.env['ir.actions.report']._get_report_from_name(self._name.replace('report.', ''))

        sale_orders = self.env[report.model].browse(docids)
        sale_order_payment_methods = self.env['sale.order.payment.method'].search(
            [('order_id', 'in', sale_orders.ids)]
        )

        if not sale_order_payment_methods:
            raise ValidationError(
                f"Sale Order(s): ({', '.join(sale_orders.mapped('name'))}) "
                f"have no Payment Methods sets, the Proforma Invoice Document can't be created!")

        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'data': data,
            'docs': sale_orders,
            'payment_methods': sale_order_payment_methods,
            'onlogic_data': sale_order_payment_methods.get_payment_method_report_data(),
        }
