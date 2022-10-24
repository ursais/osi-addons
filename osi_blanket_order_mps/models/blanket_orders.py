# Copyright (C) 2022 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class BlanketOrder(models.Model):
    _inherit = "sale.blanket.order"

    partner_ref = fields.Char(string="Partner Reference", related="partner_id.ref")
    remaining_qty_state = fields.Selection(
        [
            ("current", "Current"),
            ("past", "Past Due"),
            ("done", "Done"),
            ("expired", "Expired"),
        ],
        default="current",
        string="Remaining Qty State",
        compute="_compute_remaining_state",
        store=True,
    )

    @api.depends("line_ids", "state")
    def _compute_remaining_state(self):
        for order in self:
            if order.state == "done":
                order.remaining_qty_state = "done"
            elif order.state == "expired":
                order.remaining_qty_state = "expired"
            elif order.state == "open":
                for line in order.line_ids:
                    if (
                        line.date_schedule
                        and fields.Datetime.from_string(line.date_schedule)
                        < datetime.now()
                        and line.original_uom_qty
                        - (line.ordered_uom_qty - line.empty_ordered_uom_qty)
                        > 0
                    ):
                        order.remaining_qty_state = "past"
            else:
                order.remaining_qty_state = "current"

    def _get_sale_orders(self):
        sale_orders = self.mapped("line_ids.sale_lines.order_id")
        empty_orders = self.env["sale.order"].search(
            [("blanket_order_id2", "=", self.id)]
        )
        return empty_orders + sale_orders

    def action_mps_replenish(self, line_ids):
        mps_obj = self.env["mrp.production.schedule"]
        sale_blanket_line_obj = self.env["sale.blanket.order.line"]
        mrp_obj = self.env["mrp.production"]
        routes_id = self.env.ref(
            "mrp.route_warehouse0_manufacture", raise_if_not_found=False
        )
        line_ids = line_ids.filtered(
            lambda l: routes_id.id in l.product_id.mapped("route_ids").ids
        )
        if not line_ids:
            return True
        company_id = line_ids.mapped("order_id").mapped("company_id")[0]
        if any(not line.date_schedule for line in line_ids):
            raise UserError(_("Scheduled Date is missing in lines"))
        for line in line_ids:
            mps_id = mps_obj.search(
                [
                    ("product_id", "=", line.product_id.id),
                    ("company_id", "=", company_id.id),
                ]
            )
            if not mps_id:
                mps_id = mps_obj.create(
                    {"product_id": line.product_id.id, "min_to_replenish_qty": 0}
                )
            if mps_id:
                mps_id.forecast_ids.unlink()
                forecast = mps_id.forecast_ids
                qualiblanket_line_by_date = sale_blanket_line_obj.read_group(
                    [
                        ("product_id", "=", line.product_id.id),
                        ("order_id.state", "in", ("open", "done")),
                    ],
                    ["date_schedule", "remaining_uom_qty"],
                    ["date_schedule"],
                )
                mrp_ids = mrp_obj.search(
                    [
                        ("product_id", "=", line.product_id.id),
                        ("origin", "=", "MPS"),
                        ("state", "=", "confirmed"),
                    ],
                    order="id desc",
                )
                mrp_ids.unlink()
                for group in qualiblanket_line_by_date:
                    qty = group["remaining_uom_qty"]
                    date_schedule = datetime.strptime(group["date_schedule"], "%B %Y")
                    forecast.create(
                        {
                            "forecast_qty": qty,
                            "date": date_schedule.strftime("%Y-%m-%d"),
                            "replenish_qty": qty,
                            "replenish_qty_updated": True,
                            "production_schedule_id": mps_id.id,
                        }
                    )
                    mps_id.with_context(
                        mps_date=date_schedule.strftime("%Y-%m-%d"),
                        mps_qty=qty,
                        mps_id=mps_id.id,
                        product_id=line.product_id.id,
                    ).action_replenish()

    def action_confirm(self):
        super().action_confirm()
        for rec in self:
            rec.sudo().action_mps_replenish(rec.line_ids)
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


class BlanketOrderLine(models.Model):
    _inherit = "sale.blanket.order.line"

    empty_ordered_uom_qty = fields.Float(string="Empty Orders Qty", copy=False)
    partner_id = fields.Many2one(store=True)

    @api.depends(
        "sale_lines.order_id.state",
        "sale_lines.blanket_order_line",
        "sale_lines.product_uom_qty",
        "sale_lines.product_uom",
        "sale_lines.qty_delivered",
        "sale_lines.qty_invoiced",
        "original_uom_qty",
        "product_uom",
        "empty_ordered_uom_qty",
    )
    def _compute_quantities(self):
        res = super()._compute_quantities()
        for line in self:
            line.remaining_uom_qty = (
                line.original_uom_qty
                - line.ordered_uom_qty
                - line.empty_ordered_uom_qty
            )
        return res
