# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class Picking(models.Model):
    _inherit = "stock.picking"

    pack_barcode = fields.Char(string="Packing Barcode")

    @api.multi
    def _create_backorder(self, backorder_moves=None):
        res = super(Picking, self)._create_backorder(backorder_moves)

        if res:
            for picking in res:
                to_update = self.env['stock.picking'].search(
                    [('pack_barcode', '=', picking.backorder_id.name),
                     ('state', '!=', 'done')])
                for pick in to_update:
                    pick.pack_barcode = picking.name
