# Copyright (C) 2019 Pavlov Media
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from datetime import datetime

class ResPartnerChangeBillDate(models.TransientModel):
    _name = "res.partner.change.bill.date"

    new_date = fields.Date(string="New Date")

    @api.multi
    def action_change_date(self):
        partner_id = self.env['res.partner'].\
            browse(self.env.context.get('active_id'))
        subscription_ids = self.env['sale.subscription'].search([('partner_id', '=', partner_id.id)])
        day = self.new_date.day
        if day == 31:
            partner_id.sudo().write({'authoritative_bill_date': 'eom'})
        else:
            partner_id.sudo().write({'authoritative_bill_date': str(day)})
