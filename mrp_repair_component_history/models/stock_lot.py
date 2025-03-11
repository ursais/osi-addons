# Import Odoo libs
from odoo import fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    # COLUMNS ###

    component_history_ids = fields.One2many(
        comodel_name="component.history",
        inverse_name="lot_id",
        string="Component History",
    )

    # END #######
