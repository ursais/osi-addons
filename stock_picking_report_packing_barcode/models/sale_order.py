# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def action_confirm(self):
        super().action_confirm()

        barcode = ""

        for picking in self.picking_ids:
            if picking.location_id.name == "Packing Zone" and\
                    picking.state != "done":
                barcode = picking.name
                break
        for picking in self.picking_ids:
            if picking.location_dest_id.name == "Packing Zone":
                if barcode:
                    picking.pack_barcode = barcode
                else:
                    picking.pack_barcode = picking.name
            else:
                picking.pack_barcode = picking.name
