# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            rec = self.env['account.analytic.default'].account_get(
                self.product_id.id, self.order_id.partner_id.id, self.env.uid,
                fields.Date.today(), company_id=self.company_id.id)
            self.account_analytic_id = rec.analytic_id.id
            self.analytic_segment_one_id = rec.analytic_segment_one_id.id
            self.analytic_segment_two_id = rec.analytic_segment_two_id.id
