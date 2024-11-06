# Import Odoo libs
from odoo import fields, models


class MrpWorkorder(models.Model):
    """Inherit Work Orders to add the batch field."""

    _inherit = "mrp.workorder"

    # COLUMNS #########

    mrp_batch_id = fields.Many2one(
        string="Batch",
        related="production_id.mrp_batch_id",
    )

    # COLUMNS #########
