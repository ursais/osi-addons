# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentCheckVoid(models.Model):
    _name = "payment.check.void"
    _description = "Payment Check Void"
    _order = "check_number"

    bill_ref = fields.Char("Bill Number")
    create_date = fields.Date("Check Void Date")
    check_number = fields.Integer()
    state = fields.Selection([("void", "Void")], default="void")
    payment_id = fields.Many2one("account.payment", "Payment")
    void_reason = fields.Char()
