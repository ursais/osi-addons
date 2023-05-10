# Copyright (C) 2017 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):

    _inherit = "account.move"

    is_return_supplier = fields.Boolean(string="Return to Supplier")
    vendor_return_id = fields.Many2one(
        "vendor.product.return",
        string="Vendor Return Reference",
        readonly=True,
    )
