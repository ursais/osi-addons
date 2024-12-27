from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    mrp_note = fields.Text(
        string="MRP Note",
        related="sale_order_id.mrp_note",
        store=True
    )
