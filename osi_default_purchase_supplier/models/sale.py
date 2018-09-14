# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def generic_lines(self):
        res = False
        for line in self.order_line:
            if line.product_id.generic_flag \
                    or line.product_id.product_tmpl_id.generic_flag:
                res = True
                break
        return res

    @api.multi
    def action_confirm(self):
        if self.generic_lines():
            raise ValidationError(_(
                'Generic product exists. Order cannot be confirmed.'))
        return super(SaleOrder, self).action_confirm()
