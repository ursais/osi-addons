from odoo import api, fields, models

class SOBackorderWizard(models.TransientModel):

    _name = "sobackorder.report.wizard"
    _description = "SO Backorder Report Wizard"
        
    def action_print_report(self, data):
        data = self.env['sale.order.line'].search(['&','&','&',('exclude_from_bo_report','!=',True),('product_type','=', 'product'),('state','=', 'sale'),'|',('bo_value','!=',0),('uigd_value','!=',0)])
        return self.env.ref('osi_so_backorder_report.action_so_backorder_report').report_action(data)