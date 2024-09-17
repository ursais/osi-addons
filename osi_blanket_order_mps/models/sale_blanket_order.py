# Copyright (C) 2022 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime

from odoo import _, api, fields, models


class BlanketOrder(models.Model):
    """Inherit Blanket Orders adding MPS Integration and Field Tracking"""

    _inherit = "sale.blanket.order"

    partner_ref = fields.Char(
        string="Partner Reference",
        related="partner_id.ref",
    )
    is_mps_included = fields.Boolean(
        string="Include in Master Production Schedule (MPS)",
        default=True,
        tracking=True,
        help="For confirmed orders that are still open, adds blanket order lines to demand via the master production schedule."
    )
    state = fields.Selection(tracking=True)
    partner_id = fields.Many2one(tracking=True)
    payment_term_id = fields.Many2one(tracking=True)
    currency_id = fields.Many2one(tracking=True)
    validity_date = fields.Date(tracking=True)
    pricelist_id = fields.Many2one(tracking=True)
    user_id = fields.Many2one(tracking=True)
    team_id = fields.Many2one(tracking=True)
    client_order_ref = fields.Char(tracking=True)
    company_id = fields.Many2one(tracking=True)

    def action_mps_replenish(self, line_ids, bom_change=False):
        mps_obj = self.env["mrp.production.schedule"]
        sale_blanket_line_obj = self.env["sale.blanket.order.line"]
        mo_obj = self.env["mrp.production"]
        po_obj = self.env["purchase.order"]

        line_ids = self.line_ids.filtered(
            lambda l: l.product_id.detailed_type in ("product", "consu")
        )
        if not line_ids:
            return True
        company_id = line_ids.mapped("order_id").mapped("company_id")[0]

        for line in line_ids:
            date_schedule = line.date_schedule or line.order_id.validity_date
            if not date_schedule:
                continue
            mps_id = mps_obj.search(
                [
                    ("product_id", "=", line.product_id.id),
                    ("company_id", "=", company_id.id),
                ]
            )
            if (mps_id and bom_change) or (
                not mps_id and line.order_id.is_mps_included
            ):
                if mps_id:
                    mps_id.forecast_ids.sudo().write(
                        {"forecast_qty": 0.0, "replenish_qty": 0.0}
                    )
                    mps_id.unlink()
                mps_id = mps_obj.create(
                    {
                        "product_id": line.product_id.id,
                        "min_to_replenish_qty": 0,
                        "bom_id": line.bom_id.id,
                    }
                )
            if mps_id:
                mps_id.forecast_ids.unlink()
                forecast = mps_id.forecast_ids
                grouped_blanket_line_by_date = sale_blanket_line_obj.read_group(
                    [
                        ("product_id", "=", line.product_id.id),
                        ("order_id.state", "in", ("open", "done")),
                        ("order_id.is_mps_included", "=", True),
                    ],
                    ["date_schedule", "remaining_uom_qty"],
                    ["date_schedule"],
                )

                # Cleanup MPS MO's
                mo_ids = mo_obj.search(
                    [
                        ("product_id", "=", line.product_id.id),
                        ("origin", "=", "MPS"),
                        ("state", "=", "confirmed"),
                    ],
                    order="id desc",
                )
                mo_ids.unlink()

                # Cleanup MPS PO's
                po_ids = po_obj.search(
                    [
                        ("order_line.product_id", "=", line.product_id.id),
                        ("origin", "=", "MPS"),
                        ("state", "=", "draft"),
                    ],
                    order="id desc",
                )
                po_ids.button_cancel()
                po_ids.unlink()

                for group in grouped_blanket_line_by_date:
                    qty = group["remaining_uom_qty"]
                    date_schedule_str = group[
                        "date_schedule"
                    ]  # This could be a string or False/None

                    if (
                        not date_schedule_str
                    ):  # If it's False or None, use a fallback value
                        date_schedule_str = line.order_id.validity_date.strftime(
                            "%B %Y"
                        )

                    # Now safely parse the date string
                    date_schedule = datetime.strptime(date_schedule_str, "%B %Y")

                    # Create the forecast in MPS
                    forecast.create(
                        {
                            "forecast_qty": qty,
                            "date": date_schedule.strftime("%Y-%m-%d"),
                            "replenish_qty": qty,
                            "replenish_qty_updated": True,
                            "production_schedule_id": mps_id.id,
                            "is_edit_forcast_qty": True,
                        }
                    )
                    mps_id.with_context(
                        mps_date=date_schedule.strftime("%Y-%m-%d"),
                        mps_qty=qty,
                        mps_id=mps_id.id,
                        product_id=line.product_id.id,
                    ).action_replenish()

            # Cleanup MPS with zero forecasts
            clean_mps = mps_obj.search(
                [
                    ("forecast_ids.forecast_qty", "=", 0.0),
                    ("forecast_ids.replenish_qty", "=", 0.0),
                ]
            )
            if clean_mps:
                clean_mps.unlink()

    def action_confirm(self):
        super().action_confirm()
        for rec in self:
            rec.sudo().action_mps_replenish(rec.line_ids)
        return True

    def action_cancel(self):
        res = super().action_cancel()
        for order in self:
            order.action_mps_replenish(order.line_ids)
        return True

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        res = super().onchange_partner_id()
        for bo in self:
            partner_user = (
                bo.partner_id.user_id or bo.partner_id.commercial_partner_id.user_id
            )
            bo.user_id = partner_user.id or bo.env.context.get(
                "default_user_id", bo.env.uid
            )
        return res

    def write(self, values):
        # Store the initial state of lines and quantities before the write operation
        lines_before_write = {line.id: line.original_uom_qty for line in self.line_ids}
        line_ids_before = set(self.line_ids.ids)

        # Call the super method to perform the write operation
        res = super().write(values)

        # Track fields related to MPS replenishment
        tracking_field_list = ["line_ids", "is_mps_included"]

        # Check if any relevant field is changed and state is not draft
        if (
            any(field in values for field in tracking_field_list)
            and self.state != "draft"
        ):
            lines_after_write = {
                line.id: line.original_uom_qty for line in self.line_ids
            }
            line_ids_after = set(self.line_ids.ids)

            # Detect deleted lines or changed 'original_uom_qty'
            deleted_lines = line_ids_before - line_ids_after
            changed_qty_lines = {
                line_id
                for line_id in lines_after_write
                if line_id in lines_before_write
                and lines_after_write[line_id] != lines_before_write[line_id]
            }

            # If any line is deleted or quantity changed, trigger MPS replenishment
            if deleted_lines or changed_qty_lines or "is_mps_included" in values:
                self.action_mps_replenish(self.line_ids)

        return res
