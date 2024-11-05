from odoo import fields, models


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    mrp_batch_id = fields.Many2one(
        string="Batch",
        related="production_id.mrp_batch_id",
    )
