# Import Odoo libs
from odoo import fields, models


class StockPicking(models.Model):
    """
    Add new Sale Tags field to Stock Picking
    """

    _inherit = "stock.picking"

    # COLUMNS #####

    tag_ids = fields.Many2many(
        related="sale_id.tag_ids",
        string="Tags",
        store=False,
    )

    # END #########
