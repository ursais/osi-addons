# Import Odoo libs
from odoo import fields, models


class MrpEcoStage(models.Model):
    _inherit = "mrp.eco.stage"
    """
    Add stage to PLM ECO Stage for Tier Validation Usage
    """

    state = fields.Selection(
        [
            ("confirmed", "To Do"),
            ("progress", "In Progress"),
            ("rebase", "Rebase"),
            ("conflict", "Conflict"),
            ("done", "Done"),
            ("approved", "Approved"),
            ("cancel", "Canceled"),
        ],
        string="Approval State",
        default="progress",
        required=True,
        help="""Used by tier validations that need to trigger based on stage changes.
         Set to 'to_approve'Set to 'Approved' if the ECO stage requires approval
         before entering this stage.""",
    )
