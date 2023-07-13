# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):

    _inherit = "account.move"

    is_return_customer = fields.Boolean(string="Return from Customer")
    customer_return_id = fields.Many2one(
        "customer.product.return",
        string="Customer Return Reference",
        readonly=True,
    )
