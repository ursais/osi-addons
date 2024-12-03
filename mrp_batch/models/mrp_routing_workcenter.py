# Import Odoo libs
from odoo import api, fields, models


class MRPRoutingWorkcenter(models.Model):
    """Inherit operations to add type selection."""

    _inherit = "mrp.routing.workcenter"

    # COLUMNS #########
    type = fields.Selection(
        [
            ("build", "Build"),
            ("test", "Test"),
            ("other", "Other"),
        ],
        default="other",
        string="Type",
        required=True,
        help="The Operation Type is used to compute durations on Manfucaturing Batches.",
    )

    # END #########
    # METHODS #####

    @api.onchange("workcenter_id")
    def onchange_workcenter_id(self):
        for rec in self:
            if rec.workcenter_id.type:
                rec.type = rec.workcenter_id.type

    # END #########
