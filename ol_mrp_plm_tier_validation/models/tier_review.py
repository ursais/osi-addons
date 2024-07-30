# Import Odoo libs
from odoo import models


class TierReview(models.Model):
    """
    Add tier review history to eco's.
    """

    _inherit = "tier.review"

    # METHODS #########

    def write(self, vals):
        res = super().write(vals)
        # Create a review history record when the review is rejected/approved.
        for rec in self:
            if (
                "status" in vals
                and vals.get("status")
                and rec.status in ("rejected", "approved")
                and rec.model == "mrp.eco"
                and rec.res_id
            ):
                eco_id = self.env[rec.model].browse(rec.res_id).exists()
                if eco_id:
                    self.env["tier.validation.history"].create(
                        {
                            "eco_id": eco_id.id,
                            "definition_id": rec.definition_id.id,
                            "requested_by": rec.requested_by.id,
                            "name": rec.name,
                            "eco_stage_id": eco_id.stage_id.id,
                            "todo_by": rec.todo_by,
                            "done_by": rec.done_by.id,
                            "reviewed_date": rec.reviewed_date,
                            "comment": rec.comment,
                        }
                    )
        return res

    # END ######
