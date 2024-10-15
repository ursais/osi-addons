# Import Odoo libs
from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def get_shipping_cost(self):
        return 0.0
