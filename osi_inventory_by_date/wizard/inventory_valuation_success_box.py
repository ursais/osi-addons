from odoo import fields, models


class InventoryValuationSuccessBox(models.TransientModel):
    _name = "inventory.valuation.success.box"
    _description = "Inventory Valuation Success Box"

    file = fields.Binary(readonly=True)
    fname = fields.Char()
