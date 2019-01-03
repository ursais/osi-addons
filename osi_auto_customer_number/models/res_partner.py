# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Add customer to customer number'

    customer_number = fields.Integer(
        string='Customer Number', copy=False, readonly=True, index=True)

    @api.model
    def create(self, vals):
        if 'customer' in vals and vals.get('customer'):
            vals['customer_number'] = self.env['ir.sequence'].next_by_code(
                'res.partner.customer')

        return super(ResPartner, self).create(vals)
