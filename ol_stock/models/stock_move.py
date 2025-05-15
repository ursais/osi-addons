# Import Odoo Libs
from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    # COLUMNS #####

    note = fields.Text(string="Line Note")

    # END #########
