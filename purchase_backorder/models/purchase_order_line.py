# Copyright (C) 2021 - TODAY, Open Source Integrators
# Copyright (C) 2021 Serpent Consulting Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    last_date_received = fields.Datetime(
        compute="_compute_last_date_received", store=True
    )
    last_bill_date = fields.Datetime(compute="_compute_last_bill_date", store=True)
    uigr_qty = fields.Float(string="UIGR Qty", compute="_compute_uigr_qty", store=True)
    bo_qty = fields.Float(string="Backorder Qty", compute="_compute_bo_qty", store=True)
    uigr_value = fields.Monetary(
        string="UIGR Value", compute="_compute_uigr_value", store=True
    )
    bo_value = fields.Monetary(
        string="Backorder Value", compute="_compute_bo_value", store=True
    )
    product_type = fields.Selection(
        related="product_id.product_tmpl_id.type", string="Product Type"
    )

    @api.depends("qty_received", "product_qty")
    def _compute_bo_qty(self):
        for line in self:
            line.bo_qty = line.product_qty - line.qty_received

    @api.depends("qty_received", "qty_invoiced")
    def _compute_uigr_qty(self):
        for line in self:
            line.uigr_qty = line.qty_received - line.qty_invoiced

    @api.depends("uigr_qty", "price_unit")
    def _compute_uigr_value(self):
        for line in self:
            line.uigr_value = line.uigr_qty * line.price_unit

    @api.depends("bo_qty", "price_unit")
    def _compute_bo_value(self):
        for line in self:
            line.bo_value = line.bo_qty * line.price_unit

    @api.depends("order_id.state", "move_ids.state", "move_ids.product_uom_qty")
    def _compute_last_date_received(self):
        for line in self:
            max_date = False
            for move in line.move_ids:
                if move.state == "done":
                    if move.location_dest_id.usage == "supplier":
                        if move.to_refund:
                            continue
                    else:
                        if max_date:
                            if max_date < move.date:
                                max_date = move.date
                        else:
                            max_date = move.date
            line.last_date_received = max_date

    @api.depends("invoice_lines.move_id.state", "invoice_lines.quantity")
    def _compute_last_bill_date(self):
        for line in self:
            max_date = False
            for inv_line in line.invoice_lines:
                if inv_line.move_id.state not in ["cancel"]:
                    if inv_line.move_id.move_type == "in_invoice":
                        if max_date and inv_line.move_id.date:
                            if max_date < inv_line.move_id.date:
                                max_date = inv_line.move_id.date
                        else:
                            max_date = inv_line.move_id.date
                    elif inv_line.move_id.move_type == "in_refund":
                        continue
            line.last_bill_date = (
                max_date and max_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT) or False
            )
