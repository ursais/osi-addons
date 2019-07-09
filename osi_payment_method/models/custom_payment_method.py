# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class CustomPaymentMethod(models.Model):
    _name = "custom.payment.method"
    _description = "Payment Method"

    name = fields.Char(string="Payment Method", required=True)
    code = fields.Char(string="Code")
