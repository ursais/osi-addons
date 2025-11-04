# Import Odoo libs
from odoo import fields, models


class StockScrap(models.Model):
    """Inherit scrap to add linking fields to repairs"""

    _inherit = "stock.scrap"

    # COLUMNS ###

    repair_id = fields.Many2one(
        comodel_name="repair.order",
        string="Repair Order",
    )

    # END #######
