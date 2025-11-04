# Import Odoo libs
from odoo import fields, models


class MrpProductionBatchtag(models.Model):
    """New Object for Batch Tags."""

    _name = "mrp.production.batch.tag"
    _description = "Manufacturing Batch Tags"

    # COLUMNS #########

    name = fields.Char(
        string="Name",
        required=True,
    )
    color = fields.Integer(string="Color")

    # END #########
