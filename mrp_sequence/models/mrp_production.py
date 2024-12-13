from odoo import fields, models, api
from datetime import timedelta
import pytz


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Sequence number for scheduling within the work center.",
    )
    assigned_workcenter_id = fields.Many2one(
        "mrp.workcenter",
        string="Assigned WorkCenter",
        help="The primary assigned work center, typically where the MO will start.",
    )
    daily_sequence = fields.Integer(
        string="Daily Sequence",
        help="Sequence number for the day.",
    )

    @api.model_create_multi
    def create(self, vals):
        if "date_start" not in vals or not vals["date_start"]:
            user_tz = self.env.user.tz or "UTC"
            local_tz = pytz.timezone(user_tz)
            local_time = fields.Datetime.context_timestamp(self, fields.Datetime.now())
            vals["date_start"] = local_time.astimezone(pytz.utc)
        if "sequence" not in vals:
            vals["sequence"] = self._get_next_sequence(vals["date_start"])
        return super().create(vals)

    def _get_next_sequence(self, date_start):
        last_digit_year = date_start.strftime("%Y")[
            -1
        ]  # Extract the last digit of the year
        date_str = last_digit_year + date_start.strftime(
            "%m%d"
        )  # Construct the date string
        last_sequence = self.search(
            [
                ("date_start", ">=", date_start),
                ("date_start", "<", date_start + timedelta(days=1)),
            ],
            order="sequence desc",
            limit=1,
        ).sequence
        return last_sequence + 1 if last_sequence else int(date_str + "01")

    def _update_sequence_format(self):
        for order in self:
            last_digit_year = order.date_start.strftime("%Y")[
                -1
            ]  # Extract the last digit of the year
            date_str = last_digit_year + order.date_start.strftime(
                "%m%d"
            )  # Construct the date string
            order.with_context(skip_write=True).sequence = (
                f"{date_str}{order.assigned_workcenter_id.id:01d}{order.daily_sequence:02d}"
            )

    def write(self, vals):
        if self.env.context.get("skip_write"):
            return super().write(vals)
        res = super().write(vals)
        if "sequence" in vals or "date_start" in vals:
            self._adjust_dates()
        return res

    def _adjust_dates(self):
        for order in self:
            if order.state in ["draft", "confirmed"]:
                workcenter_orders = self.search(
                    [
                        (
                            "assigned_workcenter_id",
                            "=",
                            order.assigned_workcenter_id.id,
                        ),
                        ("state", "in", ["draft", "confirmed"]),
                        ("date_start", ">=", order.date_start.date()),
                        (
                            "date_start",
                            "<",
                            order.date_start.date() + timedelta(days=1),
                        ),
                    ],
                    order="sequence",
                )

                previous_end_time = None
                daily_sequence_counter = 1
                for mo in workcenter_orders:
                    mo.daily_sequence = daily_sequence_counter
                    daily_sequence_counter += 1
                    if previous_end_time:
                        mo.with_context(skip_write=True).date_start = previous_end_time
                    previous_end_time = mo.date_start + timedelta(
                        minutes=mo.duration_expected
                    )
                    mo._update_sequence_format()
