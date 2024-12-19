from odoo import models, fields


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    frepple_reference = fields.Char("Reference (frePPLe)")
