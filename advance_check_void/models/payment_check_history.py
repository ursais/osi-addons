# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentCheckHistory(models.Model):
    _name = "payment.check.history"
    _description = "Payment Info for the check Payment Feature"
    _order = "id desc"

    name = fields.Char(readonly=True)
    payment_id = fields.Many2one(
        "account.payment", string="Payment Info", readonly=True
    )
    partner_id = fields.Many2one("res.partner", string="Partner", readonly=True)
    amount = fields.Float("Gross Amount", readonly=True)
    check_number = fields.Integer(readonly=True)
    check_amount = fields.Float(readonly=True)
    journal_id = fields.Many2one("account.journal", "Journal", readonly=True)
    date = fields.Date(readonly=True)
    create_date = fields.Datetime(readonly=True)
    write_date = fields.Datetime(readonly=True)
    create_uid = fields.Many2one(
        comodel_name="res.users", string="Created By", readonly=True
    )
    write_uid = fields.Many2one(
        comodel_name="res.users", string="Updated By", readonly=True
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("posted", "Posted"),
            ("sent", "Sent"),
            ("void", "Void"),
            ("cancelled", "Cancelled"),
            ("reconciled", "Reconciled"),
        ],
        readonly=True,
        default="draft",
        copy=False,
        string="Status",
        tracking=True,
    )
    currency_id = fields.Many2one(
        related="payment_id.currency_id", string="Currency", readonly=True, store=True
    )
    is_visible_check = fields.Boolean(
        help="Use for the visible or invisible check number."
    )

    def _valid_field_parameter(self, field, name):
        # I can't even
        return name == "tracking" or super()._valid_field_parameter(field, name)
