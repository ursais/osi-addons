# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    brand_id = fields.Many2one('res.partner', string='Brand',
                               domain="[('type', '=', 'brand')]")

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        if self.brand_id:
            res.update({'brand_id': self.brand_id.id})
        return res
