# Import Odoo libs
from odoo import fields, models, api


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    # COLUMNS #####

    # Override the core field to make it readonly
    duration_expected = fields.Float(
        "Expected Duration",
        digits=(16, 2),
        compute="_compute_duration_expected",
        readonly=True,
        store=True,
    )  # in minutes

    # END #########
    # METHODS ##########

    @api.depends(
        "operation_id",
        "operation_id.time_cycle_manual",
        "company_id",
    )
    def _compute_duration_expected(self):
        for workorder in self:
            if workorder.state in ("done", "cancel"):
                # keep stored value, do not recompute
                continue
            value = 0.0
            if workorder.operation_id:
                value = (
                    workorder.operation_id.with_company(
                        workorder.company_id
                    ).time_cycle_manual
                    or 0.0
                )
            workorder.duration_expected = value

    # END #########
