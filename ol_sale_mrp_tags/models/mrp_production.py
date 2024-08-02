# Import Odoo libs
from odoo import fields, models


class MRPProduction(models.Model):
    """
    Add new sale and sale tag fields to Production Orders
    """

    _inherit = "mrp.production"

    # COLUMNS #####

    sale_order_id = fields.Many2one("sale.order", string="Sale Order")
    tag_ids = fields.Many2many(
        related="sale_order_id.tag_ids",
        string="Tags",
        store=False,
    )

    # END #########
