from odoo import models, fields


class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"

    mrp_batch_id = fields.Many2one(
        "mrp.production.batch",
        string="MO Batch",
        help="Manufacturing batch this transfer batch is linked to.",
    )
