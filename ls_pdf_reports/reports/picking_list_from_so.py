from odoo import api, models, fields


class ReportPickingListFromSo(models.AbstractModel):
    _name = 'report.ls_pdf_reports.report_picking_list_from_so'
    _description = 'Picking List (from Sale Order)'

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
