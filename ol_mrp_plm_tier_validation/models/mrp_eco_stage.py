# Import Odoo libs
from odoo import fields, models


class MrpEcoStage(models.Model):
    _inherit = "mrp.eco.stage"
    """
    Add stage to PLM ECO Stage for Tier Validation Usage
    """

    # COLUMNS ###

    is_approval_stage = fields.Boolean(
        string="Approval Stage",
        help="""Used by tier validations that need to trigger based on stage changes.
         Enable if tier validations need checked if the ECO moves to this stage.""",
    )
    company_id = fields.Many2one(
        "res.company", "Company", default=lambda self: self.env.company
    )

    # END #######
