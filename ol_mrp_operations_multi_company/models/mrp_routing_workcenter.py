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
    # METHODS #####

    def write(self, vals):
        # Only trigger outdated BOM if fields other than time_cycle_manual were changed
        # Add other fields as needed
        safe_fields = {
            "time_cycle_manual",
        }
        trigger_bom_flag = not set(vals.keys()).issubset(safe_fields)

        # If bom_id is changed, clear operation links before write
        if "bom_id" in vals:
            for op in self:
                op.bom_id.bom_line_ids.filtered(
                    lambda line: line.operation_id == op
                ).operation_id = False
                op.bom_id.byproduct_ids.filtered(
                    lambda byproduct: byproduct.operation_id == op
                ).operation_id = False
                op.bom_id.operation_ids.filtered(
                    lambda operation: operation.blocked_by_operation_ids == op
                ).blocked_by_operation_ids = False

        # Perform the actual write
        res = super().write(vals)

        # Mark MOs outdated *only if necessary*
        if trigger_bom_flag:
            self.bom_id._set_outdated_bom_in_productions()

        return res

    # END #########
