# Import Odoo libs
from odoo import fields, models


class MrpRoutingWorkcenter(models.Model):
    _inherit = "mrp.routing.workcenter"

    # Override the related field to make it a normal field
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        help="If set, this operation is only used for MOs in this company. "
        "Leave blank to allow the operation to be global.",
        readonly=False,
        store=True,
    )
    # Override to remove the check_company constraint
    workcenter_id = fields.Many2one(
        comodel_name="mrp.workcenter",
        string="Work Center",
        required=True,
        check_company=False,  # Important: allows cross-company linking
    )
    # Override to remove the check_company constraint
    bom_id = fields.Many2one(
        comodel_name="mrp.bom",
        string="Bill of Material",
        index=True,
        ondelete="cascade",
        required=True,
        check_company=False,  # Important: allows cross-company linking
    )

    # END #########
