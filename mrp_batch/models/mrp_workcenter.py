# Import Odoo libs
from odoo import fields, models


class MRPWorkcenter(models.Model):
    """Inherit workcenters to add type selection."""

    _inherit = "mrp.workcenter"

    # COLUMNS #########

    type = fields.Selection(
        [
            ("build", "Build"),
            ("test", "Test"),
            ("other", "Other"),
        ],
        default="other",
        string="Type",
        help="The Operation Type is used to compute durations on Manfucaturing Batches.",
    )

    # END #########
