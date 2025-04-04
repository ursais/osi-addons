# Import Odoo libs
from odoo import api, models, fields


class ReportPackingSlipFromSo(models.AbstractModel):
    _name = 'report.ol_stock.report_packing_slip_from_so'
    _description = 'Packing Slip (from Sale Order)'

    @api.model
    def _get_report_values(self, docids, data=None):

        # Get the module/report name from the class name
        report = self.env['ir.actions.report']._get_report_from_name(self._name.replace('report.', ''))

        sale_orders = self.env[report.model].browse(docids)
        stock_pickings = self.env['stock.picking'].search(
            [('sale_id', 'in', sale_orders.ids), ('picking_type_code', '=', 'outgoing')]
        )

        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'data': data,
            'docs': sale_orders,
            'stock_pickings': stock_pickings,
        }
