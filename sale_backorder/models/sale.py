# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    last_date_delivered = fields.Datetime(
        string="Last Date Delivered", compute="_compute_last_date_delivered", store=True
    )
    last_bill_date = fields.Datetime(
        string="Last Bill Date", compute="_compute_last_bill_date", store=True
    )
    uigd_value = fields.Monetary(
        string="UIGD Value", compute="_compute_uigd_value", store=True
    )
    bo_value = fields.Monetary(
        string="Backorder Value", compute="_compute_bo_value", store=True
    )

    @api.depends("order_line.uigd_value")
    def _compute_uigd_value(self):
        for order in self:
            order.uigd_value = sum(order.order_line.mapped("uigd_value"))

    @api.depends("order_line.bo_value")
    def _compute_bo_value(self):
        for order in self:
            order.bo_value = sum(order.order_line.mapped("bo_value"))

    @api.depends(
        "order_line.last_date_delivered",
        "order_line.qty_delivered",
        "order_line.qty_invoiced",
    )
    def _compute_last_date_delivered(self):
        for order in self:
            max_date = False
            for line in order.order_line:
                if line.last_date_delivered:
                    max_date = line.last_date_delivered
            order.last_date_delivered = max_date

    @api.depends(
        "order_line.last_bill_date",
        "order_line.qty_delivered",
        "order_line.qty_invoiced",
    )
    def _compute_last_bill_date(self):
        for order in self:
            max_date = False
            for line in order.order_line:
                if line.last_bill_date:
                    max_date = line.last_bill_date
            order.last_bill_date = max_date
