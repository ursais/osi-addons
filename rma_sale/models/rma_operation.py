# Copyright 2020 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo import fields, models


class RmaOperation(models.Model):
    _inherit = "rma.operation"

    sale_policy = fields.Selection(
        [
            ("no", "Not required"),
            ("ordered", "Based on Ordered Quantities"),
            ("received", "Based on Received Quantities"),
        ],
        default="no",
    )
    auto_confirm_rma_sale = fields.Boolean(
        string="Auto confirm Sales Order upon creation from RMA",
        help="When a sales is created from an RMA, automatically confirm it",
        readonly=False,
    )
    free_of_charge_rma_sale = fields.Boolean(
        string="Free of charge RMA Sales Order",
        help="Sales orders created from RMA are free of charge by default",
        readonly=False,
    )
