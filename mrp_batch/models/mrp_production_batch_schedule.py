# Import Odoo libs
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MrpProductionBatchSchedule(models.Model):
    """
    New Object for Batching Manufacturing Orders.
    The purpose is to be able to group and sort via
    sequence batch orders per day.
    """

    _name = "mrp.production.batch.schedule"
    _rec_name = "date"
    _order = "date, workcenter_tag_id"
    _description = "Manufacturing Schedule"

    # COLUMNS #########

    date = fields.Date(
        string="Date",
        required=True,
    )
    workcenter_tag_id = fields.Many2one(
        "mrp.workcenter.tag",
        string="Workcenter Tag",
        required=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    mrp_batch_ids = fields.One2many(
        "mrp.production.batch",
        "mrp_batch_schedule_id",
        string="MRP Batches",
    )

    # END #########

    def _compute_display_name(self):
        for record in self:
            record.display_name = (
                f"{record.date.strftime('%m/%d/%y')} ({record.workcenter_tag_id.name})"
                if record.date and record.workcenter_tag_id
                else "Undefined"
            )

    @api.constrains(
        "date",
        "workcenter_tag_id",
        "company_id",
    )
    def _check_unique_schedule(self):
        """Ensure no duplicate schedules exist per company, date, and workcenter tag."""
        for record in self:
            duplicate = self.search_count(
                [
                    ("id", "!=", record.id),
                    ("date", "=", record.date),
                    ("workcenter_tag_id", "=", record.workcenter_tag_id.id),
                    ("company_id", "=", record.company_id.id),
                ]
            )
            if duplicate:
                raise ValidationError(
                    "A schedule already exists for this company, date, and workcenter."
                )

    # END #########
