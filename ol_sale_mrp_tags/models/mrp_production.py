# Import Odoo libs
from odoo import fields, models


class MRPProduction(models.Model):
    _inherit = "mrp.production"

    mrp_sale_id = fields.Many2one("sale.order", string="MRP Sale ID")
    tag_ids = fields.Many2many(
        related="mrp_sale_id.tag_ids", string="Tags", store=False,
    )
