# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class resConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    sale_order_line_record_limit = fields.Integer(string="Record Limit", default=10, config_parameter='sale_order_line_record_limit')
    sale_order_status  = fields.Selection([('sale','Confirm order'),('done','Done (Locked)'),('both','Both')],string="Price History Based On", default="sale", config_parameter='sale_order_status')
    purchase_order_line_record_limit = fields.Integer(string="Record Limit", default=10, config_parameter='purchase_order_line_record_limit')
    purchase_order_status = fields.Selection([('purchase','Purchase order'),('done','Done (Locked)'),('both','Both')],string="Price History Based On", default="purchase", config_parameter='purchase_order_status')
    
    
    def get_values(self):
        res = super(resConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        sale_order_line_record_limit = ICPSudo.get_param('sale_order_line_record_limit')
        sale_order_status = ICPSudo.get_param('sale_order_status')
        purchase_order_line_record_limit = ICPSudo.get_param('purchase_order_line_record_limit')
        purchase_order_status = ICPSudo.get_param('purchase_order_status')
        res.update(
            sale_order_line_record_limit=int(sale_order_line_record_limit),
            sale_order_status=sale_order_status,
            purchase_order_line_record_limit = int(purchase_order_line_record_limit),
            purchase_order_status = purchase_order_status
        )
        return res


