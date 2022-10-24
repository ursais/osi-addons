from odoo import fields, models


class InventoryValuationSuccessBox(models.TransientModel):
    _name = "inventory.valuation.success.box"

    file = fields.Binary(readonly=True)
    fname = fields.Char()
