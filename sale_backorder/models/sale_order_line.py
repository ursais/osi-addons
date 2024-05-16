# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    last_date_delivered = fields.Datetime(
        string="Last Date Delivered", compute="_compute_last_date_delivered", store=True
    )
    last_bill_date = fields.Datetime(
        string="Last Bill Date", compute="_compute_last_bill_date", store=True
    )
    uigd_qty = fields.Float(
        string="Uninvoiced Goods Delivered Qty",
        compute="_compute_uigd_qty",
        store=True,
        help="Display a Uninvoiced Goods Delivered Qty on Order Lines.",
    )
    bo_qty = fields.Float(string="Backorder Qty", compute="_compute_bo_qty", store=True)
    uigd_value = fields.Monetary(
        string="UIGD Value", compute="_compute_uigd_value", store=True
    )
    bo_value = fields.Monetary(
        string="Backorder Value", compute="_compute_bo_value", store=True
    )
    product_type = fields.Selection(
        string="Product Type", related="product_id.product_tmpl_id.type"
    )

    @api.depends("qty_delivered", "product_uom_qty")
    def _compute_bo_qty(self):
        for line in self:
            line.bo_qty = line.product_uom_qty - line.qty_delivered

    @api.depends("qty_delivered", "qty_invoiced")
    def _compute_uigd_qty(self):
        for line in self:
            line.uigd_qty = line.qty_delivered - line.qty_invoiced

    @api.depends("uigd_qty", "price_unit")
    def _compute_uigd_value(self):
        for line in self:
            line.uigd_value = line.uigd_qty * line.price_unit

    @api.depends("bo_qty", "price_unit")
    def _compute_bo_value(self):
        for line in self:
            line.bo_value = line.bo_qty * line.price_unit

    @api.depends("qty_delivered", "qty_invoiced")
    def _compute_last_date_delivered(self):
        for line in self:
            moves = line.move_ids.filtered(
                lambda move: move.state != "done"
                or move.location_dest_id.usage != "customer"
                or not move.to_refund
            )
            if moves:
                line.last_date_delivered = moves[0].date

    @api.depends("qty_delivered", "qty_invoiced")
    def _compute_last_bill_date(self):
        for line in self:
            max_date = False
            for inv_line in line.invoice_lines:
                if (
                    inv_line.move_id.state != "cancel"
                    and inv_line.move_id.move_type == "out_invoice"
                    and inv_line.move_id.date
                ):
                    max_date = inv_line.move_id.date

            line.last_bill_date = (
                max_date and max_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT) or False
            )
