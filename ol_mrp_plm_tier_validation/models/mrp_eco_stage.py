# Import Odoo libs
from odoo import fields, models


class MrpEcoStage(models.Model):
    """
    Add stage to PLM ECO Stage for Tier Validation Usage
    """

    _inherit = "mrp.eco.stage"

    # COLUMNS ###

    is_approval_stage = fields.Boolean(
        string="Approval Stage",
        help="""Used by tier validations that need to trigger based on stage changes.
         Enable if tier validations need checked if the ECO moves to this stage.""",
    )

    # END #######
