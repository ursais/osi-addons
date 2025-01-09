# Copyright (C) 2019 - 2021, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    #Prevents price of downpayment from being reset on draft sale orders
    def action_post(self):
        downpayment_lines = {}
        for rec in self:
            downpayment_lines[rec.id] = {}
            for line in rec.invoice_line_ids:
                if line and "Down payment" in line.name:
                    downpayment_lines[rec.id][line.id] = line.price_unit
        res = super().action_post()
        for rec in self:
            for line in rec.invoice_line_ids:
                if line and "Down payment" in line.name:
                    downpayment_lines[rec.id][line.id] = line.price_unit
        return res
