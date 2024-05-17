# Copyright (C) 2021 - TODAY, Open Source Integrators
# Copyright (C) 2021 Serpent Consulting Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    last_date_received = fields.Datetime(
        compute="_compute_last_date_received", store=True
    )
    last_bill_date = fields.Datetime(compute="_compute_last_bill_date", store=True)
    uigr_value = fields.Monetary(compute="_compute_uigr_value", store=True)
    bo_value = fields.Monetary(compute="_compute_bo_value", store=True)

    @api.depends("order_line.uigr_qty", "order_line.price_unit")
    def _compute_uigr_value(self):
        for order in self:
            total = 0
            for line in order.order_line:
                total += line.uigr_value
            order.uigr_value = total

    @api.depends("order_line.bo_qty", "order_line.price_unit")
    def _compute_bo_value(self):
        for order in self:
            total = 0
            for line in order.order_line:
                total += line.bo_value
            order.bo_value = total

    @api.depends("order_line.last_date_received")
    def _compute_last_date_received(self):
        for order in self:
            max_date = False
            for line in order.order_line:
                if max_date:
                    if line.last_date_received and max_date < line.last_date_received:
                        max_date = line.last_date_received
                else:
                    max_date = line.last_date_received
            order.last_date_received = max_date

    @api.depends("order_line.last_bill_date")
    def _compute_last_bill_date(self):
        for order in self:
            max_date = False
            for line in order.order_line:
                if max_date:
                    if line.last_bill_date and max_date < line.last_bill_date:
                        max_date = line.last_bill_date
                else:
                    max_date = line.last_bill_date
            order.last_bill_date = max_date
