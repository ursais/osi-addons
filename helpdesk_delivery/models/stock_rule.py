# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom,
                               location_id, name, origin, company_id, values):
        vals = super()._get_stock_move_values(
            product_id, product_qty, product_uom,
            location_id, name, origin, company_id, values)
        vals.update({'helpdesk_ticket_id': values.get('helpdesk_ticket_id')})
        return vals
