# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class CustomPaymentMethod(models.Model):
    _name = "custom.payment.method"
    _description = "Payment Method"

    name = fields.Char(string="Payment Method")
    code = fields.Char(string="Code")





    